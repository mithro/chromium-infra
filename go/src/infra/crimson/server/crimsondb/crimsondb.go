// Copyright 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package crimsondb

import (
	"bytes"
	"database/sql"
	"fmt"
	"net"
	"strings"

	"github.com/go-sql-driver/mysql"
	"golang.org/x/net/context"

	"github.com/luci/luci-go/common/errors"
	"github.com/luci/luci-go/common/logging"

	"infra/crimson/common/datautil"
	"infra/crimson/common/netutil"
	crimson "infra/crimson/proto"
)

// IPRange describes a row in the vlan table.
type IPRange struct {
	Site      string
	VlanID    uint32
	VlanAlias string
	StartIP   string
	EndIP     string
}

func (row IPRange) String() string {
	return fmt.Sprintf("%s/%d: %s-%s (%s)",
		row.Site, row.VlanID, row.StartIP, row.EndIP, row.VlanAlias)
}

func logAndErrorf(ctx context.Context, format string, params ...interface{}) error {
	logging.Errorf(ctx, format, params...)
	return fmt.Errorf(format, params...)
}

func logAndUserErrorf(ctx context.Context, code int, format string, params ...interface{}) error {
	logging.Errorf(ctx, format, params...)
	return UserErrorf(code, format, params...)
}

// withLockedTable calls `inner` in a context of a transaction with
// the `table` locked. This guarantees an atomic update to the `table`.
func withLockedTable(ctx context.Context, table string, inner func(tx *sql.Tx) error) (err error) {
	tx, err := DB(ctx).Begin()
	if err != nil {
		logging.Errorf(ctx, "withLockedTable: failed to create a transaction: %s", err)
		return err
	}

	// Lock the whole table for global consistency. This unfortunately
	// also blocks read access for other connections. It also commits
	// the actual SQL transaction, but we don't care. The important part
	// is to reuse the same connection for all the commands, since the
	// connection is now stateful.
	_, err = tx.Exec("LOCK TABLES " + table + " WRITE")
	if err != nil {
		logging.Errorf(ctx, "Locking table '%s' failed. %s", table, err)
		tx.Rollback()
		return
	}

	defer func() {
		_, errExec := tx.Exec("UNLOCK TABLES")
		if errExec != nil {
			logging.Errorf(ctx, "Unlocking table '%s' failed. %s", table, errExec)
		}
		if err == nil {
			err = tx.Commit()
			if err != nil {
				logging.Errorf(ctx, "Committing transaction failed. %s", err)
			}
		} else {
			tx.Rollback()
		}
	}()

	err = inner(tx)
	return
}

// scanIPRanges is a low-level function to scan sql results.
// Rows must contain site, vlan_id, start_ip, end_ip, vlan_alias in that order.
func scanIPRanges(ctx context.Context, rows *sql.Rows) ([]IPRange, error) {
	var ipRanges []IPRange

	for rows.Next() {
		var startIP, endIP string
		var ip net.IP
		ipRange := IPRange{}
		err := rows.Scan(&ipRange.Site, &ipRange.VlanID, &startIP, &endIP, &ipRange.VlanAlias)
		if err != nil { // Users can't trigger that.
			cols, _ := rows.Columns()
			err = logAndErrorf(ctx, "%s. Columns: %v", err, cols)
			return nil, err
		}
		ip, err = netutil.HexStringToIP(startIP)
		if err != nil {
			return nil, err
		}
		ipRange.StartIP = ip.String()

		ip, err = netutil.HexStringToIP(endIP)
		if err != nil {
			return nil, err
		}
		ipRange.EndIP = ip.String()
		ipRanges = append(ipRanges, ipRange)
	}
	err := rows.Err()
	if err != nil {
		logging.Errorf(ctx, "%s", err)
		return nil, err
	}
	return ipRanges, nil
}

// InsertIPRange adds a new IP range in the corresponding table.
func InsertIPRange(ctx context.Context, row *crimson.IPRange) (err error) {
	if len(row.Site) == 0 {
		logging.Errorf(ctx, "Received empty site value.")
		return fmt.Errorf("Received empty site value.")
	}

	var startIP, endIP string
	startIP, err = netutil.IPStringToHexString(row.StartIp)
	if err != nil {
		return
	}
	endIP, err = netutil.IPStringToHexString(row.EndIp)
	if err != nil {
		return
	}

	// IEEE 802.1Q supports VLAN IDs 1-4094
	if row.VlanId == 0 || row.VlanId > 4094 {
		return logAndUserErrorf(ctx, InvalidArgument,
			"vlan ID in %v is invalid: must be between 1-4094; received %s", row)
	}

	// Need a transaction to guarantee the same connection for multiple
	// SQL statements.
	return withLockedTable(ctx, "vlan", func(tx *sql.Tx) error {
		// [a,b] and [c,d] overlap iff a<=d and b>=c
		statement := ("SELECT site, vlan_id, start_ip, end_ip, vlan_alias FROM vlan\n" +
			"WHERE site=? AND start_ip<=? AND end_ip>=?")
		rows, err := tx.Query(statement, row.Site, endIP, startIP)
		if err != nil {
			logging.Errorf(ctx, "IP range query failed. %s", err)
			return err
		}
		defer rows.Close()
		var ipRanges []IPRange
		ipRanges, err = scanIPRanges(ctx, rows)
		if err != nil {
			logging.Errorf(ctx, "scanIPRangeRows has failed. %s", err)
			return err
		}
		if len(ipRanges) > 0 {
			err = UserErrorf(
				AlreadyExists,
				"overlapping range(s) have been found: %s, not inserting new one", ipRanges)
			logging.Infof(ctx, "%s", err)
			return err
		}

		// No overlapping ranges have been found, insert the new one.
		logging.Infof(ctx, "No overlapping ranges have been found, proceeding.")
		statement = ("INSERT INTO vlan (site, vlan_id, start_ip, end_ip, vlan_alias)\n" +
			"VALUES (?, ?, ?, ?, ?)")
		_, err = tx.Exec(statement, row.Site, row.VlanId, startIP, endIP, row.VlanAlias)
		if err != nil {
			logging.Errorf(ctx, "IP range insertion failed. %s", err)
			return err
		}
		return nil
	})
}

// DeleteIPRange deletes an IP range from the database.
func DeleteIPRange(ctx context.Context, deleteList *crimson.IPRangeDeleteList) error {
	db := DB(ctx)

	if len(deleteList.Ranges) == 0 {
		return logAndUserErrorf(ctx, InvalidArgument,
			"Received an empty list of IP ranges to delete.")
	}

	statement := bytes.Buffer{}
	params := []interface{}{}

	statement.WriteString("DELETE FROM vlan\nWHERE ")
	delimiter := ""

	for i, r := range deleteList.Ranges {
		if len(r.Site) == 0 {
			return logAndUserErrorf(ctx, InvalidArgument,
				"Received empty site value in range %d: %s", i, r)
		}

		// IEEE 802.1Q supports VLAN IDs 1-4094
		if r.VlanId == 0 || r.VlanId > 4094 {
			return logAndUserErrorf(ctx, InvalidArgument,
				"vlan ID in %v is invalid: must be between 1-4094", r)
		}

		statement.WriteString(delimiter)
		statement.WriteString("(site=? AND vlan_id=?)")
		params = append(params, r.Site, r.VlanId)
		delimiter = "\nOR "
	}
	s := statement.String()
	// Defense in depth. We *really* don't want to drop every row at the same time.
	if strings.Index(s, "WHERE") == -1 {
		panic("Query generated does not contain a WHERE clause. " +
			"Aborting before doing something wrong.")
	}
	_, err := db.Exec(s, params...)
	if err != nil {
		logging.Errorf(ctx, "Deletion of IP ranges failed: %s", err)
		return err
	}
	return nil
}

// SelectIPRange returns ip ranges filtered by values in req.
func SelectIPRange(ctx context.Context, req *crimson.IPRangeQuery) ([]IPRange, error) {
	db := DB(ctx)
	var rows *sql.Rows
	var err error
	delimiter := ""

	statement := bytes.Buffer{}
	params := []interface{}{}

	statement.WriteString("SELECT site, vlan_id, start_ip, end_ip, vlan_alias FROM vlan")
	delimiter = "\nWHERE "

	if req.Site != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("site=?")
		params = append(params, req.Site)
	}

	if req.VlanId != 0 {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("vlan_id=?")
		params = append(params, req.VlanId)
	}

	if req.VlanAlias != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("vlan_alias=?")
		params = append(params, req.VlanAlias)
	}

	if req.Ip != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		ip, err := netutil.IPStringToHexString(req.Ip)
		if err != nil {
			return nil, UserErrorf(
				InvalidArgument,
				"parsing of IP address failed: %s", req.Ip)
		}
		statement.WriteString("start_ip<=? AND ?<=end_ip")
		params = append(params, ip, ip)
	}

	if req.Limit > 0 {
		statement.WriteString("\nLIMIT ?")
		params = append(params, req.Limit)
	}

	rows, err = db.Query(statement.String(), params...)

	if err != nil {
		logging.Errorf(ctx, "%s", err)
		return nil, err
	}
	defer rows.Close()

	var ipRanges []IPRange
	ipRanges, err = scanIPRanges(ctx, rows)
	if err != nil {
		logging.Errorf(ctx, "%s", err)
		return nil, err
	}
	return ipRanges, nil
}

// scanHosts is a low-level function to scan sql results.
// Rows must contain site, hostname, mac_addr, ip, boot_class in that order.
func scanHosts(ctx context.Context, rows *sql.Rows) (*crimson.HostList, error) {
	hostList := crimson.HostList{}

	for rows.Next() {
		var ipString, macString string
		var hw net.HardwareAddr
		var ip net.IP
		var bootClass sql.NullString

		host := crimson.Host{}
		err := rows.Scan(&host.Site, &host.Hostname, &macString, &ipString,
			&bootClass)
		if bootClass.Valid {
			host.BootClass = bootClass.String
		}
		if err != nil { // Users can't trigger that.
			logging.Errorf(ctx, "scanHost: didn't match columns: %s", err)
			return nil, err
		}
		if macString != "" {
			hw, err = netutil.HexStringToHardwareAddr(macString)
			if err != nil {
				return nil, err
			}
			host.MacAddr = hw.String()
		}

		if ipString != "" {
			ip, err = netutil.HexStringToIP(ipString)
			if err != nil {
				return nil, err
			}
			host.Ip = ip.String()
		}
		hostList.Hosts = append(hostList.Hosts, &host)
	}
	err := rows.Err()
	if err != nil {
		logging.Errorf(ctx, "scanHosts: error iterating over rows: %s", err)
		return nil, err
	}
	return &hostList, nil
}

// hostValues holds values like IP, MAC address or hostname grouped by site.
type hostValues struct {
	name     string
	sites    []string // Record the order of sites to keep tests deterministic.
	siteVals map[string][]string
}

func newHostValues(name string, size int) hostValues {
	return hostValues{
		name:     name,
		siteVals: make(map[string][]string, size),
	}
}

func (h *hostValues) Add(site, val string) {
	if _, ok := h.siteVals[site]; !ok {
		h.sites = append(h.sites, site)
	}
	h.siteVals[site] = append(h.siteVals[site], val)
}

func checkDuplicates(ctx context.Context, values hostValues, tx *sql.Tx) error {
	var params []interface{}
	statement := bytes.Buffer{}

	statement.WriteString("SELECT site, hostname, mac_addr, ip, boot_class FROM host WHERE ")
	delimiter := ""

	// WHERE (site = "site1" AND <name> IN (...)) OR (site = "site2"...)
	for _, site := range values.sites {
		vals := values.siteVals[site]
		statement.WriteString(delimiter + "(site = ? AND " + values.name + " IN (")
		params = append(params, site)
		delimiter = ""
		for _, v := range vals {
			statement.WriteString(delimiter + "?")
			delimiter = ", "
			params = append(params, v)
		}
		statement.WriteString("))")
		delimiter = " OR "
	}
	sqlRows, err := tx.Query(statement.String(), params...)
	if err != nil {
		return fmt.Errorf("checkDuplicates: failed to query: %s", err)
	}
	defer sqlRows.Close()

	rows, err := scanHosts(ctx, sqlRows)
	if len(rows.Hosts) != 0 {
		lines, errFmt := datautil.FormatHostList(rows, "text", false)
		if errFmt != nil {
			lines = []string{errFmt.Error()}
		}
		return UserErrorf(InvalidArgument,
			"Found %d existing hosts with duplicate %s: %s",
			len(rows.Hosts), values.name, strings.Join(lines, "\n"))
	}
	return nil
}

func checkDuplicateIPs(ctx context.Context, req *crimson.HostList, tx *sql.Tx) error {
	values := newHostValues("ip", len(req.Hosts))
	for i, host := range req.Hosts {
		ip, err := netutil.IPStringToHexString(host.Ip)
		if err != nil {
			return UserErrorf(InvalidArgument,
				"Failed to parse an IP %s in entry #%s: %s", host.Ip, i, err)
		}
		values.Add(host.Site, ip)
	}
	return checkDuplicates(ctx, values, tx)
}

func checkDuplicateMACs(ctx context.Context, req *crimson.HostList, tx *sql.Tx) error {
	values := newHostValues("mac_addr", len(req.Hosts))
	for i, host := range req.Hosts {
		macAddr, err := netutil.MacAddrStringToHexString(host.MacAddr)
		if err != nil {
			return UserErrorf(InvalidArgument,
				"Failed to parse a MAC %s in entry #%s: %s", host.MacAddr, i, err)
		}
		values.Add(host.Site, macAddr)
	}
	return checkDuplicates(ctx, values, tx)
}

func checkDuplicateHostnames(ctx context.Context, req *crimson.HostList, tx *sql.Tx) error {
	values := newHostValues("hostname", len(req.Hosts))
	for _, host := range req.Hosts {
		values.Add(host.Site, host.Hostname)
	}
	return checkDuplicates(ctx, values, tx)
}

// insertHostQuery composes the query template and builds its parameters.
func insertHostQuery(req *crimson.HostList) (query string, params []interface{}, err error) {
	statement := bytes.Buffer{}

	statement.WriteString("INSERT INTO host " +
		"(site, hostname, mac_addr, ip, boot_class) VALUES ")
	delimiter := ""

	for i, host := range req.Hosts {
		var ip, macAddr string
		statement.WriteString(delimiter)
		delimiter = ", "
		statement.WriteString("(?, ?, ?, ?, ?)")

		ip, err = netutil.IPStringToHexString(host.Ip)
		if err != nil {
			err = UserErrorf(InvalidArgument,
				"Failed to parse an IP %s in entry #%s: %s", host.Ip, i, err)
			return
		}

		macAddr, err = netutil.MacAddrStringToHexString(host.MacAddr)
		if err != nil {
			err = UserErrorf(InvalidArgument,
				"Failed to parse a MAC %s in entry #%s: %s", host.MacAddr, i, err)
			return
		}

		if host.BootClass == "" {
			params = append(
				params,
				host.Site, host.Hostname, macAddr, ip, nil)
		} else {
			params = append(
				params,
				host.Site, host.Hostname, macAddr, ip, host.BootClass)
		}
	}
	query = statement.String()
	return
}

func checkInsertHostArgs(req *crimson.HostList) error {
	// Check that all required fields have been provided.
	// TODO(pgervais): autogenerate missing values instead.
	for i, host := range req.Hosts {
		if host.Site == "" {
			return UserErrorf(InvalidArgument,
				"Received empty site in entry #%s", i+1)
		}
		if host.MacAddr == "" {
			return UserErrorf(InvalidArgument,
				"Received empty MAC address in entry #%s", i+1)
		}
		if host.Ip == "" {
			return UserErrorf(InvalidArgument,
				"Received empty IP address in entry #%s", i+1)
		}
		if host.Hostname == "" {
			return UserErrorf(InvalidArgument,
				"Received empty hostname in entry #%s", i+1)
		}
	}
	return nil
}

// InsertHost adds new hosts in the corresponding table.
func InsertHost(ctx context.Context, req *crimson.HostList) (err error) {
	if len(req.Hosts) == 0 {
		logging.Errorf(ctx, "Received empty list of hosts to create.")
		return UserErrorf(InvalidArgument,
			"Received empty list of hosts to create.")
	}

	if err = checkInsertHostArgs(req); err != nil {
		return
	}

	// Need a transaction to guarantee the same connection for multiple
	// SQL statements.
	return withLockedTable(ctx, "host", func(tx *sql.Tx) error {
		// Check for duplicate entries in the input.
		// TODO(sergeyberezin): make it return a single error with all the
		// duplicates listed.
		if errs := datautil.CheckDuplicateHosts(req); len(errs) > 0 {
			err = errors.NewMultiError(errs...)
			return UserErrorf(InvalidArgument, err.Error())
		}

		// Check for duplicate entries in the database.
		err := checkDuplicateIPs(ctx, req, tx)
		if err != nil {
			return err
		}

		err = checkDuplicateMACs(ctx, req, tx)
		if err != nil {
			return err
		}

		err = checkDuplicateHostnames(ctx, req, tx)
		if err != nil {
			return err
		}

		// Compose query
		query, params, err := insertHostQuery(req)
		if err != nil {
			return err
		}

		_, err = tx.Exec(query, params...)
		if err != nil {
			// MySQL error 1062 is 'duplicate entry'.
			if mysqlErr, ok := err.(*mysql.MySQLError); ok && mysqlErr.Number == 1062 {
				logging.Warningf(ctx, "Insertion of new hosts failed. %s", err)
				err = UserErrorf(AlreadyExists,
					"Hosts couldn't be created because some entries already exist.")
			}
			logging.Errorf(ctx, "Insertion of new hosts failed. %s", err)
			return err
		}
		if err != nil {
			logging.Errorf(ctx, "Opening transaction failed. %s", err)
			return err
		}
		return nil
	})
}

// SelectHost returns a list of hosts filtered by values in req.
func SelectHost(ctx context.Context, req *crimson.HostQuery) (*crimson.HostList, error) {
	var err error

	db := DB(ctx)
	delimiter := ""

	statement := bytes.Buffer{}
	params := []interface{}{}

	statement.WriteString("SELECT site, hostname, mac_addr, ip, boot_class FROM host")
	delimiter = "\nWHERE "

	if req.Site != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("site=?")
		params = append(params, req.Site)
	}

	if req.Hostname != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("hostname=?")
		params = append(params, req.Hostname)
	}

	if req.MacAddr != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		hw, err := netutil.MacAddrStringToHexString(req.MacAddr)
		if err != nil {
			return nil, UserErrorf(
				InvalidArgument,
				"parsing of Mac address failed: %s", req.MacAddr)
		}
		statement.WriteString("mac_addr=?")
		params = append(params, hw)
	}

	if req.Ip != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		ip, err := netutil.IPStringToHexString(req.Ip)
		if err != nil {
			return nil, UserErrorf(
				InvalidArgument,
				"parsing of IP address failed: %s", req.Ip)
		}
		statement.WriteString("ip=?")
		params = append(params, ip)
	}

	if req.BootClass != "" {
		statement.WriteString(delimiter)
		delimiter = "\nAND "
		statement.WriteString("boot_class=?")
		params = append(params, req.BootClass)
	}

	statement.WriteString("\nORDER BY ip")

	if req.Limit > 0 {
		statement.WriteString("\nLIMIT ?")
		params = append(params, req.Limit)
	}

	sqlRows, err := db.Query(statement.String(), params...)

	if err != nil {
		logging.Errorf(ctx, "SelectHost failed the query: %s", err)
		return nil, err
	}
	defer sqlRows.Close()

	var rows *crimson.HostList
	rows, err = scanHosts(ctx, sqlRows)
	if err != nil {
		logging.Errorf(ctx, "SelectHost failed to scan the rows: %s", err)
		return nil, err
	}
	return rows, nil
}

// DeleteHost drops hosts whose name match criteria in req.
func DeleteHost(ctx context.Context, req *crimson.HostDeleteList) error {
	var err error

	db := DB(ctx)
	delimiter := ""

	statement := bytes.Buffer{}
	params := []interface{}{}

	// Having a 'WHERE' in this string is very important to avoid issuing
	// 'DELETE FROM host;' by mistake ;-)
	statement.WriteString("DELETE FROM host\nWHERE ")
	delimiter = "("

	for _, host := range req.Hosts {
		if host.Hostname == "" && host.MacAddr == "" {
			return fmt.Errorf("Host must be selected by either hostname or mac " +
				"address. Got empty strings in both cases.")
		}

		if host.Hostname != "" {
			statement.WriteString(delimiter)
			delimiter = " AND "
			statement.WriteString("hostname=?")
			params = append(params, host.Hostname)
		}
		if host.MacAddr != "" {
			statement.WriteString(delimiter)
			delimiter = " AND "
			statement.WriteString("mac_addr=?")
			mac, err := netutil.MacAddrStringToHexString(host.MacAddr)
			if err != nil {
				return UserErrorf(InvalidArgument, "Invalid MAC address: %s", host.MacAddr)
			}
			params = append(params, mac)
		}

		statement.WriteString(")")
		delimiter = "\nOR ("
	}

	// Defense in depth. We *really* don't want to drop every row at the same time.
	s := statement.String()
	if strings.Index(s, "WHERE") == -1 {
		panic("Query generated does not contain a WHERE clause. " +
			"Aborting before doing something wrong.")
	}
	_, err = db.Exec(statement.String(), params...)
	// TODO(pgervais): return the number of rows affected.
	if err != nil {
		logging.Errorf(ctx, "Deletion of hosts failed. %s", err)
		return err
	}
	return nil
}

type ctxKeyType int

const ctxKey = ctxKeyType(0)

// UseDB stores a db handle into a context.
func UseDB(ctx context.Context, db *sql.DB) context.Context {
	return context.WithValue(ctx, ctxKey, db)
}

// DB gets the current db handle from the context.
func DB(ctx context.Context) *sql.DB {
	return ctx.Value(ctxKey).(*sql.DB)
}

// GetDBHandle returns a handle to the Cloud SQL instance used by this deployment.
func GetDBHandle() (*sql.DB, error) {
	// TODO(pgervais): do not hard-code the name of the database.
	db, err := sql.Open("mysql", "root@cloudsql(crimson-staging:crimson-staging)/crimson")
	if err != nil {
		return nil, err
	}
	// AppEngine instance can have at most 12 concurrent
	// connections. Additional connections would fail with 'error 2'.
	db.SetMaxOpenConns(12)
	return db, nil
}
