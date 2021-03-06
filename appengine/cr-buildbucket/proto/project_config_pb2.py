# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: project_config.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='project_config.proto',
  package='buildbucket',
  syntax='proto2',
  serialized_pb=_b('\n\x14project_config.proto\x12\x0b\x62uildbucket\"z\n\x03\x41\x63l\x12#\n\x04role\x18\x01 \x01(\x0e\x32\x15.buildbucket.Acl.Role\x12\r\n\x05group\x18\x02 \x01(\t\x12\x10\n\x08identity\x18\x03 \x01(\t\"-\n\x04Role\x12\n\n\x06READER\x10\x00\x12\r\n\tSCHEDULER\x10\x01\x12\n\n\x06WRITER\x10\x02\"\xba\x05\n\x08Swarming\x12\x10\n\x08hostname\x18\x01 \x01(\t\x12\x12\n\nurl_format\x18\x02 \x01(\t\x12\x37\n\x10\x62uilder_defaults\x18\x03 \x01(\x0b\x32\x1d.buildbucket.Swarming.Builder\x12/\n\x08\x62uilders\x18\x04 \x03(\x0b\x32\x1d.buildbucket.Swarming.Builder\x12\'\n\x1ftask_template_canary_percentage\x18\x05 \x01(\r\x1aT\n\x06Recipe\x12\x12\n\nrepository\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x12\n\nproperties\x18\x03 \x03(\t\x12\x14\n\x0cproperties_j\x18\x04 \x03(\t\x1a\x9e\x03\n\x07\x42uilder\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x10\n\x08\x63\x61tegory\x18\x06 \x01(\t\x12\x15\n\rswarming_tags\x18\x02 \x03(\t\x12\x12\n\ndimensions\x18\x03 \x03(\t\x12@\n\rcipd_packages\x18\x08 \x03(\x0b\x32).buildbucket.Swarming.Builder.CipdPackage\x12,\n\x06recipe\x18\x04 \x01(\x0b\x32\x1c.buildbucket.Swarming.Recipe\x12\x10\n\x08priority\x18\x05 \x01(\r\x12\x1e\n\x16\x65xecution_timeout_secs\x18\x07 \x01(\r\x12\x38\n\x06\x63\x61\x63hes\x18\t \x03(\x0b\x32(.buildbucket.Swarming.Builder.CacheEntry\x1a\x42\n\x0b\x43ipdPackage\x12\x14\n\x0cpackage_name\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x0f\n\x07version\x18\x03 \x01(\t\x1a(\n\nCacheEntry\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\"_\n\x06\x42ucket\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x1e\n\x04\x61\x63ls\x18\x02 \x03(\x0b\x32\x10.buildbucket.Acl\x12\'\n\x08swarming\x18\x03 \x01(\x0b\x32\x15.buildbucket.Swarming\"6\n\x0e\x42uildbucketCfg\x12$\n\x07\x62uckets\x18\x01 \x03(\x0b\x32\x13.buildbucket.Bucket')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_ACL_ROLE = _descriptor.EnumDescriptor(
  name='Role',
  full_name='buildbucket.Acl.Role',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='READER', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SCHEDULER', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='WRITER', index=2, number=2,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=114,
  serialized_end=159,
)
_sym_db.RegisterEnumDescriptor(_ACL_ROLE)


_ACL = _descriptor.Descriptor(
  name='Acl',
  full_name='buildbucket.Acl',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='role', full_name='buildbucket.Acl.role', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='group', full_name='buildbucket.Acl.group', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='identity', full_name='buildbucket.Acl.identity', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _ACL_ROLE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=37,
  serialized_end=159,
)


_SWARMING_RECIPE = _descriptor.Descriptor(
  name='Recipe',
  full_name='buildbucket.Swarming.Recipe',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='repository', full_name='buildbucket.Swarming.Recipe.repository', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='name', full_name='buildbucket.Swarming.Recipe.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='properties', full_name='buildbucket.Swarming.Recipe.properties', index=2,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='properties_j', full_name='buildbucket.Swarming.Recipe.properties_j', index=3,
      number=4, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=359,
  serialized_end=443,
)

_SWARMING_BUILDER_CIPDPACKAGE = _descriptor.Descriptor(
  name='CipdPackage',
  full_name='buildbucket.Swarming.Builder.CipdPackage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='package_name', full_name='buildbucket.Swarming.Builder.CipdPackage.package_name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='path', full_name='buildbucket.Swarming.Builder.CipdPackage.path', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='version', full_name='buildbucket.Swarming.Builder.CipdPackage.version', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=752,
  serialized_end=818,
)

_SWARMING_BUILDER_CACHEENTRY = _descriptor.Descriptor(
  name='CacheEntry',
  full_name='buildbucket.Swarming.Builder.CacheEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='buildbucket.Swarming.Builder.CacheEntry.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='path', full_name='buildbucket.Swarming.Builder.CacheEntry.path', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=820,
  serialized_end=860,
)

_SWARMING_BUILDER = _descriptor.Descriptor(
  name='Builder',
  full_name='buildbucket.Swarming.Builder',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='buildbucket.Swarming.Builder.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='category', full_name='buildbucket.Swarming.Builder.category', index=1,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='swarming_tags', full_name='buildbucket.Swarming.Builder.swarming_tags', index=2,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='dimensions', full_name='buildbucket.Swarming.Builder.dimensions', index=3,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='cipd_packages', full_name='buildbucket.Swarming.Builder.cipd_packages', index=4,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='recipe', full_name='buildbucket.Swarming.Builder.recipe', index=5,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='priority', full_name='buildbucket.Swarming.Builder.priority', index=6,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='execution_timeout_secs', full_name='buildbucket.Swarming.Builder.execution_timeout_secs', index=7,
      number=7, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='caches', full_name='buildbucket.Swarming.Builder.caches', index=8,
      number=9, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_SWARMING_BUILDER_CIPDPACKAGE, _SWARMING_BUILDER_CACHEENTRY, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=446,
  serialized_end=860,
)

_SWARMING = _descriptor.Descriptor(
  name='Swarming',
  full_name='buildbucket.Swarming',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='hostname', full_name='buildbucket.Swarming.hostname', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='url_format', full_name='buildbucket.Swarming.url_format', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='builder_defaults', full_name='buildbucket.Swarming.builder_defaults', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='builders', full_name='buildbucket.Swarming.builders', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='task_template_canary_percentage', full_name='buildbucket.Swarming.task_template_canary_percentage', index=4,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_SWARMING_RECIPE, _SWARMING_BUILDER, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=162,
  serialized_end=860,
)


_BUCKET = _descriptor.Descriptor(
  name='Bucket',
  full_name='buildbucket.Bucket',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='buildbucket.Bucket.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='acls', full_name='buildbucket.Bucket.acls', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='swarming', full_name='buildbucket.Bucket.swarming', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=862,
  serialized_end=957,
)


_BUILDBUCKETCFG = _descriptor.Descriptor(
  name='BuildbucketCfg',
  full_name='buildbucket.BuildbucketCfg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='buckets', full_name='buildbucket.BuildbucketCfg.buckets', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=959,
  serialized_end=1013,
)

_ACL.fields_by_name['role'].enum_type = _ACL_ROLE
_ACL_ROLE.containing_type = _ACL
_SWARMING_RECIPE.containing_type = _SWARMING
_SWARMING_BUILDER_CIPDPACKAGE.containing_type = _SWARMING_BUILDER
_SWARMING_BUILDER_CACHEENTRY.containing_type = _SWARMING_BUILDER
_SWARMING_BUILDER.fields_by_name['cipd_packages'].message_type = _SWARMING_BUILDER_CIPDPACKAGE
_SWARMING_BUILDER.fields_by_name['recipe'].message_type = _SWARMING_RECIPE
_SWARMING_BUILDER.fields_by_name['caches'].message_type = _SWARMING_BUILDER_CACHEENTRY
_SWARMING_BUILDER.containing_type = _SWARMING
_SWARMING.fields_by_name['builder_defaults'].message_type = _SWARMING_BUILDER
_SWARMING.fields_by_name['builders'].message_type = _SWARMING_BUILDER
_BUCKET.fields_by_name['acls'].message_type = _ACL
_BUCKET.fields_by_name['swarming'].message_type = _SWARMING
_BUILDBUCKETCFG.fields_by_name['buckets'].message_type = _BUCKET
DESCRIPTOR.message_types_by_name['Acl'] = _ACL
DESCRIPTOR.message_types_by_name['Swarming'] = _SWARMING
DESCRIPTOR.message_types_by_name['Bucket'] = _BUCKET
DESCRIPTOR.message_types_by_name['BuildbucketCfg'] = _BUILDBUCKETCFG

Acl = _reflection.GeneratedProtocolMessageType('Acl', (_message.Message,), dict(
  DESCRIPTOR = _ACL,
  __module__ = 'project_config_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.Acl)
  ))
_sym_db.RegisterMessage(Acl)

Swarming = _reflection.GeneratedProtocolMessageType('Swarming', (_message.Message,), dict(

  Recipe = _reflection.GeneratedProtocolMessageType('Recipe', (_message.Message,), dict(
    DESCRIPTOR = _SWARMING_RECIPE,
    __module__ = 'project_config_pb2'
    # @@protoc_insertion_point(class_scope:buildbucket.Swarming.Recipe)
    ))
  ,

  Builder = _reflection.GeneratedProtocolMessageType('Builder', (_message.Message,), dict(

    CipdPackage = _reflection.GeneratedProtocolMessageType('CipdPackage', (_message.Message,), dict(
      DESCRIPTOR = _SWARMING_BUILDER_CIPDPACKAGE,
      __module__ = 'project_config_pb2'
      # @@protoc_insertion_point(class_scope:buildbucket.Swarming.Builder.CipdPackage)
      ))
    ,

    CacheEntry = _reflection.GeneratedProtocolMessageType('CacheEntry', (_message.Message,), dict(
      DESCRIPTOR = _SWARMING_BUILDER_CACHEENTRY,
      __module__ = 'project_config_pb2'
      # @@protoc_insertion_point(class_scope:buildbucket.Swarming.Builder.CacheEntry)
      ))
    ,
    DESCRIPTOR = _SWARMING_BUILDER,
    __module__ = 'project_config_pb2'
    # @@protoc_insertion_point(class_scope:buildbucket.Swarming.Builder)
    ))
  ,
  DESCRIPTOR = _SWARMING,
  __module__ = 'project_config_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.Swarming)
  ))
_sym_db.RegisterMessage(Swarming)
_sym_db.RegisterMessage(Swarming.Recipe)
_sym_db.RegisterMessage(Swarming.Builder)
_sym_db.RegisterMessage(Swarming.Builder.CipdPackage)
_sym_db.RegisterMessage(Swarming.Builder.CacheEntry)

Bucket = _reflection.GeneratedProtocolMessageType('Bucket', (_message.Message,), dict(
  DESCRIPTOR = _BUCKET,
  __module__ = 'project_config_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.Bucket)
  ))
_sym_db.RegisterMessage(Bucket)

BuildbucketCfg = _reflection.GeneratedProtocolMessageType('BuildbucketCfg', (_message.Message,), dict(
  DESCRIPTOR = _BUILDBUCKETCFG,
  __module__ = 'project_config_pb2'
  # @@protoc_insertion_point(class_scope:buildbucket.BuildbucketCfg)
  ))
_sym_db.RegisterMessage(BuildbucketCfg)


# @@protoc_insertion_point(module_scope)
