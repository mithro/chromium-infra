// Copyright (c) 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package cipd

import (
	"encoding/json"
	"io/ioutil"
	"os"
	"path/filepath"

	local "github.com/luci/luci-go/cipd/client/cipd/local"
	"github.com/luci/luci-go/common/logging"
	"github.com/luci/luci-go/common/tsmon"
	"github.com/luci/luci-go/common/tsmon/field"
	"github.com/luci/luci-go/common/tsmon/metric"
	"golang.org/x/net/context"
)

var (
	packageInstanceID = metric.NewString("cipd/packages/deployed/instance_id",
		"instance ids of deployed packages.",
		nil,
		field.String("package_name"))
)

// Register adds tsmon callbacks to set cipd metrics.
func Register() {
	tsmon.RegisterCallback(func(c context.Context) {
		if err := update(c); err != nil {
			logging.Errorf(c, "Failed to update CIPD metrics: %s", err)
		}
	})
}

func exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func listCIPDVersionFiles(path string) []string {
	var ret []string

	pythonVersion := filepath.Join(path, "CIPD_VERSION.json")
	if exists(pythonVersion) {
		ret = append(ret, pythonVersion)
	}

	matches, err := filepath.Glob(filepath.Join(path, "*.cipd_version"))
	if err != nil {
		panic(err) // Only happens on malformed patterns.
	}

	ret = append(ret, matches...)
	return ret
}

func readCIPDVersionFile(path string) (local.VersionFile, error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return local.VersionFile{}, nil
	}

	var ret local.VersionFile
	err = json.Unmarshal(data, &ret)
	return ret, err
}

func update(c context.Context) error {
	for _, path := range versionDirs {
		logging.Infof(c, "Looking for CIPD packages in %s", path)
		for _, filePath := range listCIPDVersionFiles(path) {
			logging.Infof(c, "Reading CIPD file %s", filePath)
			v, err := readCIPDVersionFile(filePath)
			if err != nil {
				logging.Warningf(c, "Error reading CIPD version file %s: %s", filePath, err)
				continue
			}
			packageInstanceID.Set(c, v.InstanceID, v.PackageName)
		}
	}
	return nil
}
