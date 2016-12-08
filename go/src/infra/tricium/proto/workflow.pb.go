// Code generated by protoc-gen-go.
// source: infra/tricium/proto/workflow.proto
// DO NOT EDIT!

package tricium

import proto "github.com/golang/protobuf/proto"
import fmt "fmt"
import math "math"

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

// Tricium workflow configuration.
//
// Workflow configurations are typically generated from a Tricium configuration.
type Workflow struct {
	Worker []*Worker `protobuf:"bytes,1,rep,name=worker" json:"worker,omitempty"`
}

func (m *Workflow) Reset()                    { *m = Workflow{} }
func (m *Workflow) String() string            { return proto.CompactTextString(m) }
func (*Workflow) ProtoMessage()               {}
func (*Workflow) Descriptor() ([]byte, []int) { return fileDescriptor3, []int{0} }

func (m *Workflow) GetWorker() []*Worker {
	if m != nil {
		return m.Worker
	}
	return nil
}

// A Tricium worker includes the details needed to execute an analyzer on a
// specific platform as swarming task.
type Worker struct {
	// Name of worker is a mangled name from the analyzer name and the platform,
	// e.g, ‘GitFileIsolator_linux’.
	Name string `protobuf:"bytes,1,opt,name=name" json:"name,omitempty"`
	// Includes data dependencies for runtime type checking.
	Needs    Data_Type `protobuf:"varint,2,opt,name=needs,enum=tricium.Data_Type" json:"needs,omitempty"`
	Provides Data_Type `protobuf:"varint,3,opt,name=provides,enum=tricium.Data_Type" json:"provides,omitempty"`
	// Workers to run after this one.
	Next []string `protobuf:"bytes,4,rep,name=next" json:"next,omitempty"`
	// Swarming dimensions for execution of the worker. These should be on the
	// form "key:value", using keys and values known to the swarming service.
	Dimensions []string `protobuf:"bytes,5,rep,name=dimensions" json:"dimensions,omitempty"`
	// List of cipd packages needed on the swarming task use to execute the
	// worker.
	CipdPackage []*CipdPackage `protobuf:"bytes,6,rep,name=cipd_package,json=cipdPackage" json:"cipd_package,omitempty"`
	// Command use to execute the worker.
	Cmd *Cmd `protobuf:"bytes,7,opt,name=cmd" json:"cmd,omitempty"`
	// Deadline for execution of the worker in minutes.  Note that this time
	// should include the overhead of triggering the corresponding swarming task
	// and to collect result from it.
	Deadline int32 `protobuf:"varint,8,opt,name=deadline" json:"deadline,omitempty"`
}

func (m *Worker) Reset()                    { *m = Worker{} }
func (m *Worker) String() string            { return proto.CompactTextString(m) }
func (*Worker) ProtoMessage()               {}
func (*Worker) Descriptor() ([]byte, []int) { return fileDescriptor3, []int{1} }

func (m *Worker) GetCipdPackage() []*CipdPackage {
	if m != nil {
		return m.CipdPackage
	}
	return nil
}

func (m *Worker) GetCmd() *Cmd {
	if m != nil {
		return m.Cmd
	}
	return nil
}

func init() {
	proto.RegisterType((*Workflow)(nil), "tricium.Workflow")
	proto.RegisterType((*Worker)(nil), "tricium.Worker")
}

func init() { proto.RegisterFile("infra/tricium/proto/workflow.proto", fileDescriptor3) }

var fileDescriptor3 = []byte{
	// 286 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x09, 0x6e, 0x88, 0x02, 0xff, 0x74, 0x90, 0xbd, 0x4e, 0xc3, 0x30,
	0x14, 0x85, 0x95, 0xa6, 0x4d, 0xc3, 0x6d, 0x05, 0x92, 0xc5, 0x60, 0x75, 0xa8, 0xac, 0x2e, 0x78,
	0x4a, 0xa5, 0x76, 0xe0, 0x01, 0xe0, 0x01, 0x90, 0x85, 0xd4, 0x11, 0x19, 0xfb, 0x16, 0x59, 0xad,
	0x7f, 0xe4, 0x04, 0x5a, 0x9e, 0x86, 0x57, 0x45, 0x71, 0xa2, 0x94, 0xa1, 0x6c, 0xb9, 0xe7, 0xfb,
	0x72, 0x8f, 0x6d, 0x58, 0x19, 0xb7, 0x8f, 0x72, 0xdd, 0x44, 0xa3, 0xcc, 0xa7, 0x5d, 0x87, 0xe8,
	0x1b, 0xbf, 0x3e, 0xf9, 0x78, 0xd8, 0x1f, 0xfd, 0xa9, 0x4a, 0x23, 0x99, 0xf6, 0x74, 0xb1, 0xbc,
	0x26, 0x6b, 0xd9, 0xc8, 0x4e, 0x5c, 0xb0, 0x6b, 0x5c, 0x79, 0x6b, 0xbd, 0xeb, 0x8c, 0xd5, 0x16,
	0xca, 0x5d, 0xbf, 0x9c, 0x3c, 0x40, 0xd1, 0x16, 0x61, 0xa4, 0x19, 0xcb, 0xf9, 0x6c, 0x73, 0x57,
	0xf5, 0x3f, 0x56, 0xbb, 0x14, 0x8b, 0x1e, 0xaf, 0x7e, 0x46, 0x50, 0x74, 0x11, 0x21, 0x30, 0x76,
	0xd2, 0x22, 0xcd, 0x58, 0xc6, 0x6f, 0x44, 0xfa, 0x26, 0x1c, 0x26, 0x0e, 0x51, 0xd7, 0x74, 0xc4,
	0x32, 0x7e, 0xbb, 0x21, 0xc3, 0x9a, 0xe7, 0xf6, 0x64, 0xaf, 0xdf, 0x01, 0x45, 0x27, 0x90, 0x0a,
	0xca, 0x10, 0xfd, 0x97, 0xd1, 0x58, 0xd3, 0xfc, 0x5f, 0x79, 0x70, 0x52, 0x1b, 0x9e, 0x1b, 0x3a,
	0x66, 0x79, 0x6a, 0xc3, 0x73, 0x43, 0x96, 0x00, 0xda, 0x58, 0x74, 0xb5, 0xf1, 0xae, 0xa6, 0x93,
	0x44, 0xfe, 0x24, 0xe4, 0x11, 0xe6, 0xca, 0x04, 0xfd, 0x16, 0xa4, 0x3a, 0xc8, 0x0f, 0xa4, 0x45,
	0xba, 0xdb, 0xfd, 0xd0, 0xf3, 0x64, 0x82, 0x7e, 0xe9, 0x98, 0x98, 0xa9, 0xcb, 0x40, 0x96, 0x90,
	0x2b, 0xab, 0xe9, 0x94, 0x65, 0x7c, 0xb6, 0x99, 0x5f, 0x7c, 0xab, 0x45, 0x0b, 0xc8, 0x02, 0x4a,
	0x8d, 0x52, 0x1f, 0x8d, 0x43, 0x5a, 0xb2, 0x8c, 0x4f, 0xc4, 0x30, 0xbf, 0x17, 0xe9, 0x75, 0xb7,
	0xbf, 0x01, 0x00, 0x00, 0xff, 0xff, 0x60, 0xea, 0xc5, 0x32, 0xce, 0x01, 0x00, 0x00,
}