# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is govered by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

# This file implements the discovery service, originally described here:
# https://godoc.org/github.com/luci/luci-go/grpc/discovery
# This service keeps track of all services which have been registered via
# add_service, and the autogenerated FileDescriptors which are in the files
# defining those services' inputs and outputs.
#
# This service is used automatically from prpc/grpc/__init__:Server.


from discovery import service_pb2


class DiscoveryServicer(service_pb2.DiscoveryServicer):

  def __init__(self):
    """Create an empty discovery servicer."""
    super(DiscoveryServicer, self).__init__()
    self._services = set()
    self._file_descriptors = set()

  def add_service(self, generic_handler):
    """Register a service handler with the discovery service.

    Args:
      generic_handler: a grpc.types.GenericRpcHandler
    """
    self._services.add(generic_handler.service_name)

  def add_file(self, proto_module):
    """Register a file with the discovery service.

    Args:
      proto_module: a module object for an imported autogenerated _pb2.py file
    """
    self._file_descriptors.add(proto_module.DESCRIPTOR)

  def Describe(self, request, context):
    """Return a DescribeResponse with all service names and file descriptors."""
    response = service_pb2.DescribeResponse()
    for service in sorted(self._services):
      response.services.append(service)
    for file_descriptor in sorted(
        self._file_descriptors, key=lambda fd: fd.name):
      new = response.description.file.add()
      file_descriptor.CopyToProto(new)
    return response