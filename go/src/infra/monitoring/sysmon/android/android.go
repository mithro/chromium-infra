// Copyright (c) 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package android

import (
	"os/user"
	"path/filepath"
	"regexp"

	"github.com/luci/luci-go/common/logging"
	"github.com/luci/luci-go/common/tsmon"
	"github.com/luci/luci-go/common/tsmon/field"
	"github.com/luci/luci-go/common/tsmon/metric"
	"github.com/luci/luci-go/common/tsmon/types"
	"golang.org/x/net/context"
)

var (
	cpuTemp = metric.NewFloat("dev/mobile/cpu/temperature",
		"device CPU temperature in deg C",
		&types.MetricMetadata{Units: types.DegreeCelsiusUnit},
		field.String("device_id"))
	battTemp = metric.NewFloat("dev/mobile/battery/temperature",
		"battery temperature in deg C",
		&types.MetricMetadata{Units: types.DegreeCelsiusUnit},
		field.String("device_id"))
	battCharge = metric.NewFloat("dev/mobile/battery/charge",
		"percentage charge of battery",
		nil,
		field.String("device_id"))
	devStatus = metric.NewString("dev/mobile/status",
		"operational state of device",
		nil,
		field.String("device_id"))
	devType = metric.NewString("dev/mobile/type",
		"device hardware or type",
		nil,
		field.String("device_id"))
	devOS = metric.NewString("dev/mobile/os",
		"operating system of the device",
		nil,
		field.String("device_id"))
	devUptime = metric.NewFloat("dev/mobile/uptime",
		"device uptime in seconds",
		&types.MetricMetadata{Units: types.Seconds},
		field.String("device_id"))

	memFree = metric.NewInt("dev/mobile/mem/free",
		"available memory (free + cached + buffers) in kb",
		&types.MetricMetadata{Units: types.Kibibytes},
		field.String("device_id"))
	memTotal = metric.NewInt("dev/mobile/mem/total",
		"total memory (device ram - kernel leaks) in kb",
		&types.MetricMetadata{Units: types.Kibibytes},
		field.String("device_id"))

	procCount = metric.NewInt("dev/mobile/proc/count",
		"process count",
		nil,
		field.String("device_id"))

	metricReadStatus = metric.NewString("dev/android_device_metric_read/status",
		"status of the last metric read",
		nil)

	portPathRE = regexp.MustCompile(`\d+/\d+`)
)

// Register adds tsmon callbacks to set android metrics.
func Register() {
	tsmon.RegisterCallback(func(c context.Context) {
		if err := update(c); err != nil {
			logging.Errorf(c, "Failed to update Android metrics: %s", err)
		}
	})
}

func update(c context.Context) error {
	usr, err := user.Current()
	if err != nil {
		return err
	}

	file, status, err := loadFile(c, filepath.Join(usr.HomeDir, fileName))
	metricReadStatus.Set(c, status)
	if err != nil {
		return err
	}

	updateFromFile(c, file)
	return nil
}

func updateFromFile(c context.Context, f deviceStatusFile) {
	for name, d := range f.Devices {
		if portPathRE.FindStringIndex(name) != nil {
			logging.Warningf(c, "Found port path '%s' as device ID, skipping", name)
			continue
		}

		cpuTemp.Set(c, d.Temp.EMMCTherm, name)
		battTemp.Set(c, d.Battery.GetTemperature(), name)
		battCharge.Set(c, d.Battery.Level, name)
		devOS.Set(c, d.Build.ID, name)
		devStatus.Set(c, d.GetStatus(), name)
		devType.Set(c, d.Build.GetName(), name)
		devUptime.Set(c, d.Uptime, name)
		memFree.Set(c, d.Mem.Avail, name)
		memTotal.Set(c, d.Mem.Total, name)
		procCount.Set(c, d.Processes, name)
	}
}