// Code generated by protoc-gen-go.
// source: infra/tools/kitchen/proto/arguments.proto
// DO NOT EDIT!

/*
Package recipe_engine is a generated protocol buffer package.

It is generated from these files:
	infra/tools/kitchen/proto/arguments.proto
	infra/tools/kitchen/proto/package.proto

It has these top-level messages:
	Arguments
	DepSpec
	Package
*/
package recipe_engine

import proto "github.com/golang/protobuf/proto"
import fmt "fmt"
import math "math"

// Reference imports to suppress errors if they are not otherwise used.
var _ = proto.Marshal
var _ = fmt.Errorf
var _ = math.Inf

// This is a compile-time assertion to ensure that this generated file
// is compatible with the proto package it is being compiled against.
// A compilation error at this line likely means your copy of the
// proto package needs to be updated.
const _ = proto.ProtoPackageIsVersion2 // please upgrade the proto package

// Arguments is a protobuf that can be supplied to the recipe engine through its
// "--operational-args-path" command-line parameter in JSONPB format.
type Arguments struct {
	// Input Properties.
	Properties *Arguments_PropertyMap `protobuf:"bytes,1,opt,name=properties" json:"properties,omitempty"`
	// Annotation control flags.
	AnnotationFlags *Arguments_AnnotationFlags `protobuf:"bytes,2,opt,name=annotation_flags,json=annotationFlags" json:"annotation_flags,omitempty"`
	Logdog          *Arguments_LogDogFlags     `protobuf:"bytes,3,opt,name=logdog" json:"logdog,omitempty"`
	EngineFlags     *Arguments_EngineFlags     `protobuf:"bytes,4,opt,name=engine_flags,json=engineFlags" json:"engine_flags,omitempty"`
}

func (m *Arguments) Reset()                    { *m = Arguments{} }
func (m *Arguments) String() string            { return proto.CompactTextString(m) }
func (*Arguments) ProtoMessage()               {}
func (*Arguments) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0} }

func (m *Arguments) GetProperties() *Arguments_PropertyMap {
	if m != nil {
		return m.Properties
	}
	return nil
}

func (m *Arguments) GetAnnotationFlags() *Arguments_AnnotationFlags {
	if m != nil {
		return m.AnnotationFlags
	}
	return nil
}

func (m *Arguments) GetLogdog() *Arguments_LogDogFlags {
	if m != nil {
		return m.Logdog
	}
	return nil
}

func (m *Arguments) GetEngineFlags() *Arguments_EngineFlags {
	if m != nil {
		return m.EngineFlags
	}
	return nil
}

// A single recipe engine Property value.
type Arguments_Property struct {
	// The property value.
	//
	// Types that are valid to be assigned to Value:
	//	*Arguments_Property_S
	//	*Arguments_Property_Int
	//	*Arguments_Property_Uint
	//	*Arguments_Property_D
	//	*Arguments_Property_B
	//	*Arguments_Property_Data
	//	*Arguments_Property_Map
	//	*Arguments_Property_List
	Value isArguments_Property_Value `protobuf_oneof:"value"`
}

func (m *Arguments_Property) Reset()                    { *m = Arguments_Property{} }
func (m *Arguments_Property) String() string            { return proto.CompactTextString(m) }
func (*Arguments_Property) ProtoMessage()               {}
func (*Arguments_Property) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 0} }

type isArguments_Property_Value interface {
	isArguments_Property_Value()
}

type Arguments_Property_S struct {
	S string `protobuf:"bytes,1,opt,name=s,oneof"`
}
type Arguments_Property_Int struct {
	Int int64 `protobuf:"varint,2,opt,name=int,oneof"`
}
type Arguments_Property_Uint struct {
	Uint uint64 `protobuf:"varint,3,opt,name=uint,oneof"`
}
type Arguments_Property_D struct {
	D float64 `protobuf:"fixed64,4,opt,name=d,oneof"`
}
type Arguments_Property_B struct {
	B bool `protobuf:"varint,5,opt,name=b,oneof"`
}
type Arguments_Property_Data struct {
	Data []byte `protobuf:"bytes,6,opt,name=data,proto3,oneof"`
}
type Arguments_Property_Map struct {
	Map *Arguments_PropertyMap `protobuf:"bytes,7,opt,name=map,oneof"`
}
type Arguments_Property_List struct {
	List *Arguments_PropertyList `protobuf:"bytes,8,opt,name=list,oneof"`
}

func (*Arguments_Property_S) isArguments_Property_Value()    {}
func (*Arguments_Property_Int) isArguments_Property_Value()  {}
func (*Arguments_Property_Uint) isArguments_Property_Value() {}
func (*Arguments_Property_D) isArguments_Property_Value()    {}
func (*Arguments_Property_B) isArguments_Property_Value()    {}
func (*Arguments_Property_Data) isArguments_Property_Value() {}
func (*Arguments_Property_Map) isArguments_Property_Value()  {}
func (*Arguments_Property_List) isArguments_Property_Value() {}

func (m *Arguments_Property) GetValue() isArguments_Property_Value {
	if m != nil {
		return m.Value
	}
	return nil
}

func (m *Arguments_Property) GetS() string {
	if x, ok := m.GetValue().(*Arguments_Property_S); ok {
		return x.S
	}
	return ""
}

func (m *Arguments_Property) GetInt() int64 {
	if x, ok := m.GetValue().(*Arguments_Property_Int); ok {
		return x.Int
	}
	return 0
}

func (m *Arguments_Property) GetUint() uint64 {
	if x, ok := m.GetValue().(*Arguments_Property_Uint); ok {
		return x.Uint
	}
	return 0
}

func (m *Arguments_Property) GetD() float64 {
	if x, ok := m.GetValue().(*Arguments_Property_D); ok {
		return x.D
	}
	return 0
}

func (m *Arguments_Property) GetB() bool {
	if x, ok := m.GetValue().(*Arguments_Property_B); ok {
		return x.B
	}
	return false
}

func (m *Arguments_Property) GetData() []byte {
	if x, ok := m.GetValue().(*Arguments_Property_Data); ok {
		return x.Data
	}
	return nil
}

func (m *Arguments_Property) GetMap() *Arguments_PropertyMap {
	if x, ok := m.GetValue().(*Arguments_Property_Map); ok {
		return x.Map
	}
	return nil
}

func (m *Arguments_Property) GetList() *Arguments_PropertyList {
	if x, ok := m.GetValue().(*Arguments_Property_List); ok {
		return x.List
	}
	return nil
}

// XXX_OneofFuncs is for the internal use of the proto package.
func (*Arguments_Property) XXX_OneofFuncs() (func(msg proto.Message, b *proto.Buffer) error, func(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error), func(msg proto.Message) (n int), []interface{}) {
	return _Arguments_Property_OneofMarshaler, _Arguments_Property_OneofUnmarshaler, _Arguments_Property_OneofSizer, []interface{}{
		(*Arguments_Property_S)(nil),
		(*Arguments_Property_Int)(nil),
		(*Arguments_Property_Uint)(nil),
		(*Arguments_Property_D)(nil),
		(*Arguments_Property_B)(nil),
		(*Arguments_Property_Data)(nil),
		(*Arguments_Property_Map)(nil),
		(*Arguments_Property_List)(nil),
	}
}

func _Arguments_Property_OneofMarshaler(msg proto.Message, b *proto.Buffer) error {
	m := msg.(*Arguments_Property)
	// value
	switch x := m.Value.(type) {
	case *Arguments_Property_S:
		b.EncodeVarint(1<<3 | proto.WireBytes)
		b.EncodeStringBytes(x.S)
	case *Arguments_Property_Int:
		b.EncodeVarint(2<<3 | proto.WireVarint)
		b.EncodeVarint(uint64(x.Int))
	case *Arguments_Property_Uint:
		b.EncodeVarint(3<<3 | proto.WireVarint)
		b.EncodeVarint(uint64(x.Uint))
	case *Arguments_Property_D:
		b.EncodeVarint(4<<3 | proto.WireFixed64)
		b.EncodeFixed64(math.Float64bits(x.D))
	case *Arguments_Property_B:
		t := uint64(0)
		if x.B {
			t = 1
		}
		b.EncodeVarint(5<<3 | proto.WireVarint)
		b.EncodeVarint(t)
	case *Arguments_Property_Data:
		b.EncodeVarint(6<<3 | proto.WireBytes)
		b.EncodeRawBytes(x.Data)
	case *Arguments_Property_Map:
		b.EncodeVarint(7<<3 | proto.WireBytes)
		if err := b.EncodeMessage(x.Map); err != nil {
			return err
		}
	case *Arguments_Property_List:
		b.EncodeVarint(8<<3 | proto.WireBytes)
		if err := b.EncodeMessage(x.List); err != nil {
			return err
		}
	case nil:
	default:
		return fmt.Errorf("Arguments_Property.Value has unexpected type %T", x)
	}
	return nil
}

func _Arguments_Property_OneofUnmarshaler(msg proto.Message, tag, wire int, b *proto.Buffer) (bool, error) {
	m := msg.(*Arguments_Property)
	switch tag {
	case 1: // value.s
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeStringBytes()
		m.Value = &Arguments_Property_S{x}
		return true, err
	case 2: // value.int
		if wire != proto.WireVarint {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeVarint()
		m.Value = &Arguments_Property_Int{int64(x)}
		return true, err
	case 3: // value.uint
		if wire != proto.WireVarint {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeVarint()
		m.Value = &Arguments_Property_Uint{x}
		return true, err
	case 4: // value.d
		if wire != proto.WireFixed64 {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeFixed64()
		m.Value = &Arguments_Property_D{math.Float64frombits(x)}
		return true, err
	case 5: // value.b
		if wire != proto.WireVarint {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeVarint()
		m.Value = &Arguments_Property_B{x != 0}
		return true, err
	case 6: // value.data
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		x, err := b.DecodeRawBytes(true)
		m.Value = &Arguments_Property_Data{x}
		return true, err
	case 7: // value.map
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		msg := new(Arguments_PropertyMap)
		err := b.DecodeMessage(msg)
		m.Value = &Arguments_Property_Map{msg}
		return true, err
	case 8: // value.list
		if wire != proto.WireBytes {
			return true, proto.ErrInternalBadWireType
		}
		msg := new(Arguments_PropertyList)
		err := b.DecodeMessage(msg)
		m.Value = &Arguments_Property_List{msg}
		return true, err
	default:
		return false, nil
	}
}

func _Arguments_Property_OneofSizer(msg proto.Message) (n int) {
	m := msg.(*Arguments_Property)
	// value
	switch x := m.Value.(type) {
	case *Arguments_Property_S:
		n += proto.SizeVarint(1<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(len(x.S)))
		n += len(x.S)
	case *Arguments_Property_Int:
		n += proto.SizeVarint(2<<3 | proto.WireVarint)
		n += proto.SizeVarint(uint64(x.Int))
	case *Arguments_Property_Uint:
		n += proto.SizeVarint(3<<3 | proto.WireVarint)
		n += proto.SizeVarint(uint64(x.Uint))
	case *Arguments_Property_D:
		n += proto.SizeVarint(4<<3 | proto.WireFixed64)
		n += 8
	case *Arguments_Property_B:
		n += proto.SizeVarint(5<<3 | proto.WireVarint)
		n += 1
	case *Arguments_Property_Data:
		n += proto.SizeVarint(6<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(len(x.Data)))
		n += len(x.Data)
	case *Arguments_Property_Map:
		s := proto.Size(x.Map)
		n += proto.SizeVarint(7<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(s))
		n += s
	case *Arguments_Property_List:
		s := proto.Size(x.List)
		n += proto.SizeVarint(8<<3 | proto.WireBytes)
		n += proto.SizeVarint(uint64(s))
		n += s
	case nil:
	default:
		panic(fmt.Sprintf("proto: unexpected type %T in oneof", x))
	}
	return n
}

// An ordered list of Properties.
type Arguments_PropertyList struct {
	Property []*Arguments_Property `protobuf:"bytes,1,rep,name=property" json:"property,omitempty"`
}

func (m *Arguments_PropertyList) Reset()                    { *m = Arguments_PropertyList{} }
func (m *Arguments_PropertyList) String() string            { return proto.CompactTextString(m) }
func (*Arguments_PropertyList) ProtoMessage()               {}
func (*Arguments_PropertyList) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 1} }

func (m *Arguments_PropertyList) GetProperty() []*Arguments_Property {
	if m != nil {
		return m.Property
	}
	return nil
}

// A map of properties bound to string name keys.
type Arguments_PropertyMap struct {
	// A map of property key to value.
	Property map[string]*Arguments_Property `protobuf:"bytes,1,rep,name=property" json:"property,omitempty" protobuf_key:"bytes,1,opt,name=key" protobuf_val:"bytes,2,opt,name=value"`
}

func (m *Arguments_PropertyMap) Reset()                    { *m = Arguments_PropertyMap{} }
func (m *Arguments_PropertyMap) String() string            { return proto.CompactTextString(m) }
func (*Arguments_PropertyMap) ProtoMessage()               {}
func (*Arguments_PropertyMap) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 2} }

func (m *Arguments_PropertyMap) GetProperty() map[string]*Arguments_Property {
	if m != nil {
		return m.Property
	}
	return nil
}

// Message containing the set of supported annotation control flags.
type Arguments_AnnotationFlags struct {
	// If true, emit CURRENT_TIMESTAMP annotations.
	EmitTimestamp bool `protobuf:"varint,1,opt,name=emit_timestamp,json=emitTimestamp" json:"emit_timestamp,omitempty"`
	// If true, emit all input properties as annotations at the beginning of
	// recipe engine execution.
	EmitInitialProperties bool `protobuf:"varint,2,opt,name=emit_initial_properties,json=emitInitialProperties" json:"emit_initial_properties,omitempty"`
}

func (m *Arguments_AnnotationFlags) Reset()                    { *m = Arguments_AnnotationFlags{} }
func (m *Arguments_AnnotationFlags) String() string            { return proto.CompactTextString(m) }
func (*Arguments_AnnotationFlags) ProtoMessage()               {}
func (*Arguments_AnnotationFlags) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 3} }

func (m *Arguments_AnnotationFlags) GetEmitTimestamp() bool {
	if m != nil {
		return m.EmitTimestamp
	}
	return false
}

func (m *Arguments_AnnotationFlags) GetEmitInitialProperties() bool {
	if m != nil {
		return m.EmitInitialProperties
	}
	return false
}

// LogDog flags.
//
// If the "streamserver_uri" is provided, recipe output will be forwarded
// through LogDog streams using Milo's Annotation Protobuf instead of
// STDOUT/STDERR and classic @@@annotations@@@.
type Arguments_LogDogFlags struct {
	// The LogDog streamserver URI.
	StreamserverUri string `protobuf:"bytes,1,opt,name=streamserver_uri,json=streamserverUri" json:"streamserver_uri,omitempty"`
	// The log stream base name. If provided, generated stream names will be
	// prefixed with "<name_base>/". This must be a valid LogDog stream name.
	NameBase string `protobuf:"bytes,2,opt,name=name_base,json=nameBase" json:"name_base,omitempty"`
	// If true, tee output through STDOUT/STDERR using inline @@@annotation@@@
	// markers in addition to LogDog streaming.
	Tee bool `protobuf:"varint,3,opt,name=tee" json:"tee,omitempty"`
	// If not empty, this is a path where the final annotation protobuf should
	// be dumped on completion.
	FinalAnnotationDumpPath string `protobuf:"bytes,4,opt,name=final_annotation_dump_path,json=finalAnnotationDumpPath" json:"final_annotation_dump_path,omitempty"`
}

func (m *Arguments_LogDogFlags) Reset()                    { *m = Arguments_LogDogFlags{} }
func (m *Arguments_LogDogFlags) String() string            { return proto.CompactTextString(m) }
func (*Arguments_LogDogFlags) ProtoMessage()               {}
func (*Arguments_LogDogFlags) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 4} }

func (m *Arguments_LogDogFlags) GetStreamserverUri() string {
	if m != nil {
		return m.StreamserverUri
	}
	return ""
}

func (m *Arguments_LogDogFlags) GetNameBase() string {
	if m != nil {
		return m.NameBase
	}
	return ""
}

func (m *Arguments_LogDogFlags) GetTee() bool {
	if m != nil {
		return m.Tee
	}
	return false
}

func (m *Arguments_LogDogFlags) GetFinalAnnotationDumpPath() string {
	if m != nil {
		return m.FinalAnnotationDumpPath
	}
	return ""
}

// Any flags to pass to the recipe engine. Used to toggle on new behavior,
// like sending logs through logdog.
type Arguments_EngineFlags struct {
	// If true, emit recipe execution results using a result.proto
	UseResultProto bool `protobuf:"varint,1,opt,name=use_result_proto,json=useResultProto" json:"use_result_proto,omitempty"`
}

func (m *Arguments_EngineFlags) Reset()                    { *m = Arguments_EngineFlags{} }
func (m *Arguments_EngineFlags) String() string            { return proto.CompactTextString(m) }
func (*Arguments_EngineFlags) ProtoMessage()               {}
func (*Arguments_EngineFlags) Descriptor() ([]byte, []int) { return fileDescriptor0, []int{0, 5} }

func (m *Arguments_EngineFlags) GetUseResultProto() bool {
	if m != nil {
		return m.UseResultProto
	}
	return false
}

func init() {
	proto.RegisterType((*Arguments)(nil), "recipe_engine.Arguments")
	proto.RegisterType((*Arguments_Property)(nil), "recipe_engine.Arguments.Property")
	proto.RegisterType((*Arguments_PropertyList)(nil), "recipe_engine.Arguments.PropertyList")
	proto.RegisterType((*Arguments_PropertyMap)(nil), "recipe_engine.Arguments.PropertyMap")
	proto.RegisterType((*Arguments_AnnotationFlags)(nil), "recipe_engine.Arguments.AnnotationFlags")
	proto.RegisterType((*Arguments_LogDogFlags)(nil), "recipe_engine.Arguments.LogDogFlags")
	proto.RegisterType((*Arguments_EngineFlags)(nil), "recipe_engine.Arguments.EngineFlags")
}

func init() { proto.RegisterFile("infra/tools/kitchen/proto/arguments.proto", fileDescriptor0) }

var fileDescriptor0 = []byte{
	// 581 bytes of a gzipped FileDescriptorProto
	0x1f, 0x8b, 0x08, 0x00, 0x00, 0x09, 0x6e, 0x88, 0x02, 0xff, 0x8c, 0x54, 0xdf, 0x6e, 0xd3, 0x3e,
	0x14, 0x9e, 0x97, 0x6e, 0x4b, 0x4e, 0xf6, 0xa7, 0xb2, 0x7e, 0x3f, 0x2d, 0x0a, 0x37, 0x05, 0x31,
	0x29, 0xbb, 0x69, 0xa5, 0x21, 0xb1, 0x89, 0xc1, 0xc5, 0xa6, 0x0d, 0x86, 0xb4, 0xa1, 0xca, 0xc0,
	0x2d, 0x91, 0xbb, 0xba, 0xa9, 0xb5, 0xc4, 0xb1, 0x6c, 0x67, 0x52, 0x9f, 0x81, 0xd7, 0xe0, 0x35,
	0x78, 0x31, 0xae, 0x90, 0x9d, 0xb4, 0x4b, 0x41, 0xa8, 0xbd, 0xf3, 0xf9, 0xce, 0xf7, 0x7d, 0x39,
	0xe7, 0xf8, 0x38, 0x70, 0xcc, 0xc5, 0x44, 0xd1, 0x81, 0x29, 0xcb, 0x5c, 0x0f, 0x1e, 0xb8, 0xb9,
	0x9f, 0x32, 0x31, 0x90, 0xaa, 0x34, 0xe5, 0x80, 0xaa, 0xac, 0x2a, 0x98, 0x30, 0xba, 0xef, 0x62,
	0xbc, 0xa7, 0xd8, 0x3d, 0x97, 0x2c, 0x65, 0x22, 0xe3, 0x82, 0xbd, 0xf8, 0x1e, 0x40, 0x70, 0x31,
	0xa7, 0xe0, 0x2b, 0x00, 0xa9, 0x4a, 0xc9, 0x94, 0xe1, 0x4c, 0x47, 0xa8, 0x87, 0x92, 0xf0, 0xe4,
	0x65, 0x7f, 0x49, 0xd1, 0x5f, 0xb0, 0xfb, 0xc3, 0x9a, 0x3a, 0xbb, 0xa3, 0x92, 0xb4, 0x74, 0xf8,
	0x33, 0x74, 0xa9, 0x10, 0xa5, 0xa1, 0x86, 0x97, 0x22, 0x9d, 0xe4, 0x34, 0xd3, 0xd1, 0xa6, 0xf3,
	0x4a, 0xfe, 0xe9, 0x75, 0xb1, 0x10, 0xbc, 0xb7, 0x7c, 0x72, 0x40, 0x97, 0x01, 0xfc, 0x16, 0xb6,
	0xf3, 0x32, 0x1b, 0x97, 0x59, 0xe4, 0xad, 0x28, 0xeb, 0xb6, 0xcc, 0xae, 0xca, 0xac, 0xb6, 0x69,
	0x34, 0xf8, 0x03, 0xec, 0xd6, 0xbc, 0xa6, 0x9c, 0xce, 0x0a, 0x8f, 0x6b, 0x07, 0xd4, 0x1e, 0x21,
	0x7b, 0x0a, 0xe2, 0x5f, 0x08, 0xfc, 0x79, 0xdf, 0x78, 0x1f, 0x50, 0x3d, 0xa5, 0xe0, 0x66, 0x83,
	0x20, 0x8d, 0x31, 0x78, 0x5c, 0x18, 0xd7, 0xab, 0x77, 0xb3, 0x41, 0x6c, 0x80, 0xff, 0x83, 0x4e,
	0x65, 0x41, 0x5b, 0x75, 0xe7, 0x66, 0x83, 0xb8, 0xc8, 0x2a, 0xc7, 0xae, 0x08, 0x64, 0x95, 0x63,
	0x1b, 0x8f, 0xa2, 0xad, 0x1e, 0x4a, 0x7c, 0x1b, 0x8f, 0xac, 0x6a, 0x4c, 0x0d, 0x8d, 0xb6, 0x7b,
	0x28, 0xd9, 0xb5, 0x2a, 0x1b, 0xe1, 0x33, 0xf0, 0x0a, 0x2a, 0xa3, 0x9d, 0xf5, 0xef, 0xc5, 0x56,
	0x51, 0x50, 0x89, 0xcf, 0xa1, 0x93, 0x73, 0x6d, 0x22, 0xdf, 0x49, 0x8f, 0x56, 0x4a, 0x6f, 0xb9,
	0x36, 0xf6, 0xb3, 0x56, 0x74, 0xb9, 0x03, 0x5b, 0x8f, 0x34, 0xaf, 0x58, 0x7c, 0x07, 0xbb, 0x6d,
	0x02, 0x7e, 0x07, 0x7e, 0x73, 0xed, 0xb3, 0x08, 0xf5, 0xbc, 0x24, 0x3c, 0x79, 0xbe, 0xd2, 0x99,
	0x2c, 0x24, 0xf1, 0x4f, 0x04, 0x61, 0xab, 0x56, 0xfc, 0xe9, 0x2f, 0xbb, 0x93, 0x75, 0x7a, 0x5c,
	0x9c, 0xaf, 0x85, 0x51, 0x6d, 0xff, 0x6f, 0xb0, 0xb7, 0x94, 0xc2, 0x5d, 0xf0, 0x1e, 0xd8, 0xac,
	0xbe, 0x31, 0x62, 0x8f, 0xf8, 0xb4, 0x69, 0xad, 0xd9, 0xcf, 0x35, 0xca, 0xaf, 0xf9, 0x6f, 0x36,
	0xcf, 0x50, 0x2c, 0xe1, 0xe0, 0x8f, 0xb5, 0xc5, 0x47, 0xb0, 0xcf, 0x0a, 0x6e, 0x52, 0xc3, 0x0b,
	0xa6, 0x0d, 0x2d, 0xa4, 0xfb, 0x98, 0x4f, 0xf6, 0x2c, 0xfa, 0x65, 0x0e, 0xe2, 0xd7, 0x70, 0xe8,
	0x68, 0x5c, 0x70, 0xc3, 0x69, 0x9e, 0xb6, 0x1e, 0xdd, 0xa6, 0xe3, 0xff, 0x6f, 0xd3, 0x1f, 0xeb,
	0xec, 0x70, 0x91, 0x8c, 0x7f, 0x20, 0x08, 0x5b, 0xeb, 0x8d, 0x8f, 0xa1, 0xab, 0x8d, 0x62, 0xb4,
	0xd0, 0x4c, 0x3d, 0x32, 0x95, 0x56, 0x8a, 0x37, 0xdd, 0x1d, 0xb4, 0xf1, 0xaf, 0x8a, 0xe3, 0x67,
	0x10, 0x08, 0x5a, 0xb0, 0x74, 0x44, 0x75, 0xdd, 0x6d, 0x40, 0x7c, 0x0b, 0x5c, 0x52, 0xcd, 0xec,
	0x60, 0x0c, 0x63, 0x6e, 0x47, 0x7d, 0x62, 0x8f, 0xf8, 0x1c, 0xe2, 0x09, 0x17, 0x34, 0x4f, 0x5b,
	0x2f, 0x79, 0x5c, 0x15, 0x32, 0x95, 0xd4, 0x4c, 0xdd, 0xe6, 0x06, 0xe4, 0xd0, 0x31, 0x9e, 0x46,
	0x70, 0x55, 0x15, 0x72, 0x48, 0xcd, 0x34, 0x3e, 0x85, 0xb0, 0xf5, 0x80, 0x70, 0x02, 0xdd, 0x4a,
	0xb3, 0x54, 0x31, 0x5d, 0xe5, 0x26, 0x75, 0xbf, 0xa1, 0x66, 0x2c, 0xfb, 0x95, 0x66, 0xc4, 0xc1,
	0x43, 0x8b, 0x8e, 0xb6, 0x5d, 0xf2, 0xd5, 0xef, 0x00, 0x00, 0x00, 0xff, 0xff, 0x67, 0x2f, 0x70,
	0x23, 0xd0, 0x04, 0x00, 0x00,
}
