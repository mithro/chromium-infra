// Copyright 2017 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package tracker

import (
	"fmt"
	"strings"

	ds "github.com/luci/gae/service/datastore"
	"github.com/luci/luci-go/common/logging"

	"golang.org/x/net/context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"

	"infra/tricium/api/admin/v1"
	"infra/tricium/appengine/common/track"
)

// WorkerDone tracks the completion of a worker.
func (*trackerServer) WorkerDone(c context.Context, req *admin.WorkerDoneRequest) (*admin.WorkerDoneResponse, error) {
	if req.RunId == 0 {
		return nil, grpc.Errorf(codes.InvalidArgument, "missing run ID")
	}
	if req.Worker == "" {
		return nil, grpc.Errorf(codes.InvalidArgument, "missing worker")
	}
	if req.IsolatedOutputHash == "" {
		return nil, grpc.Errorf(codes.InvalidArgument, "missing output hash")
	}
	// TODO(emso): check exit code
	if err := workerDone(c, req); err != nil {
		return nil, grpc.Errorf(codes.Internal, "failed to track worker completion: %v", err)
	}
	return &admin.WorkerDoneResponse{}, nil
}

func workerDone(c context.Context, req *admin.WorkerDoneRequest) error {
	logging.Infof(c, "[tracker] Worker done (run ID: %s, worker: %s)", req.RunId, req.Worker)
	runKey, analyzerKey, workerKey := createKeys(c, req.RunId, req.Worker)
	// Prepare to update worker state.
	worker := &track.WorkerInvocation{
		ID:     workerKey.StringID(),
		Parent: workerKey.Parent(),
	}
	// TODO(emso): add DoneFailure if results
	// TODO(emso): add result details from isolated output.
	workerState := track.DoneSuccess
	if req.ExitCode != 0 {
		workerState = track.DoneException
	}
	// Prepare to update state of analyzer invocation.
	analyzer := &track.AnalyzerInvocation{
		ID:     analyzerKey.StringID(),
		Parent: analyzerKey.Parent(),
	}
	var workers []*track.WorkerInvocation
	if err := ds.GetAll(c, ds.NewQuery("WorkerInvocation").Ancestor(analyzerKey), &workers); err != nil {
		return fmt.Errorf("failed to retrieve worker invocations: %v", err)
	}
	analyzerState := track.DoneSuccess
	for _, w := range workers {
		if w.Name == req.Worker {
			w.State = workerState // Setting state to what we will store in the below transaction.
		}
		// When all workers are done, aggregate the result.
		// All worker DoneSuccess -> analyzer DoneSuccess
		// One or more workers DoneFailure -> analyzer DoneFailure
		// If not DoneFailure, then one or more workers DoneException -> analyzer DoneException
		if w.State.IsDone() {
			if w.State == track.DoneFailure {
				analyzerState = track.DoneFailure
			} else if w.State == track.DoneException && analyzer.State == track.DoneSuccess {
				analyzerState = track.DoneException
			}
		} else {
			// Found non-done worker, no change to be made - abort.
			analyzerState = track.Launched // reset to launched.
			break
		}
	}
	// Prepare to update run state.
	run := &track.Run{ID: runKey.IntID()}
	var analyzers []*track.AnalyzerInvocation
	if err := ds.GetAll(c, ds.NewQuery("AnalyzerInvocation").Ancestor(runKey), &analyzers); err != nil {
		return fmt.Errorf("failed to retrieve analyzer invocations: %v", err)
	}
	analyzerName := strings.Split(req.Worker, "_")[0]
	runState := track.DoneSuccess
	for _, a := range analyzers {
		if a.Name == analyzerName {
			a.State = analyzerState // Setting state to what will be stored in the below transaction.
		}
		// When all analyzers are done, aggregate the result.
		// All analyzers DoneSuccess -> run DoneSuccess
		// One or more analyzers DoneFailure -> run DoneFailure
		// If not DoneFailure, then one or more analyzers DoneException -> run DoneException
		if a.State.IsDone() {
			if a.State == track.DoneFailure {
				runState = track.DoneFailure
			} else if a.State == track.DoneException && runState == track.DoneSuccess {
				runState = track.DoneException
			}
		} else {
			// Found non-done analyzer, nothing to update - abort.
			runState = track.Launched // reset to launched.
			break
		}
	}
	return ds.RunInTransaction(c, func(c context.Context) (err error) {
		// Run the below three operations in parallel, make room for two errors.
		errors := 2
		done := make(chan error, errors)
		defer func() {
			for i := 0; i < errors; i++ {
				if err2 := <-done; err2 != nil {
					err = err2
					break // stop after the first error.
				}
			}
		}()
		go func() {
			// Update worker state.
			if err := ds.Get(c, worker); err != nil {
				done <- fmt.Errorf("failed to retrieve worker: %v", err)
				return
			}
			if worker.State != workerState {
				worker.State = workerState
				if err := ds.Put(c, worker); err != nil {
					done <- fmt.Errorf("failed to mark worker as done-*: %v", err)
					return
				}
			}
			done <- nil
		}()
		go func() {
			// Update analyzer state.
			if err := ds.Get(c, analyzer); err != nil {
				done <- fmt.Errorf("failed to retrieve analyzer: %v", err)
				return
			}
			if analyzer.State != analyzerState {
				analyzer.State = analyzerState
				if err := ds.Put(c, analyzer); err != nil {
					done <- fmt.Errorf("failed to mark analyzer as done-*: %v", err)
					return
				}
			}
			done <- nil
		}()
		// Update run state.
		if err := ds.Get(c, run); err != nil {
			return fmt.Errorf("failed to retrieve run: %v", err)
		}
		if run.State != runState {
			run.State = runState
			if err := ds.Put(c, run); err != nil {
				return fmt.Errorf("failed to mark run as done-*: %v", err)
			}
		}
		return nil
	}, nil)
}

func createKeys(c context.Context, runID int64, worker string) (*ds.Key, *ds.Key, *ds.Key) {
	runKey := ds.NewKey(c, "Run", "", runID, nil)
	// Assuming that the analyzer name is included in the worker name, before the first underscore.
	analyzerName := strings.Split(worker, "_")[0]
	analyzerKey := ds.NewKey(c, "AnalyzerInvocation", analyzerName, 0, runKey)
	return runKey, analyzerKey, ds.NewKey(c, "WorkerInvocation", worker, 0, analyzerKey)
}
