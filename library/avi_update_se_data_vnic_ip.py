#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_serviceengine
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ServiceEngine Avi RESTful Object
description:
    - This module is used to configure ServiceEngine object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    availability_zone:
        description:
            - Availability_zone of serviceengine.
    cloud_ref:
        description:
            - It is a reference to an object of type cloud.
    container_mode:
        description:
            - Boolean flag to set container_mode.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    container_type:
        description:
            - Enum options - container_type_bridge, container_type_host, container_type_host_dpdk.
            - Default value when not specified in API or module is interpreted by Avi Controller as CONTAINER_TYPE_HOST.
    controller_created:
        description:
            - Boolean flag to set controller_created.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    controller_ip:
        description:
            - Controller_ip of serviceengine.
    data_vnics:
        description:
            - List of vnic.
    enable_state:
        description:
            - Inorder to disable se set this field appropriately.
            - Enum options - SE_STATE_ENABLED, SE_STATE_DISABLED_FOR_PLACEMENT, SE_STATE_DISABLED, SE_STATE_DISABLED_FORCE.
            - Default value when not specified in API or module is interpreted by Avi Controller as SE_STATE_ENABLED.
    flavor:
        description:
            - Flavor of serviceengine.
    host_ref:
        description:
            - It is a reference to an object of type vimgrhostruntime.
    hypervisor:
        description:
            - Enum options - default, vmware_esx, kvm, vmware_vsan, xen.
    mgmt_vnic:
        description:
            - Vnic settings for serviceengine.
    name:
        description:
            - Name of the object.
            - Default value when not specified in API or module is interpreted by Avi Controller as VM name unknown.
    resources:
        description:
            - Seresources settings for serviceengine.
    se_group_ref:
        description:
            - It is a reference to an object of type serviceenginegroup.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create ServiceEngine object
  avi_serviceengine:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_serviceengine
"""

RETURN = '''
obj:
    description: ServiceEngine (api/serviceengine) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from avi.sdk.utils.ansible_utils import avi_common_argument_spec
    from pkg_resources import parse_version
    import avi.sdk
    sdk_version = getattr(avi.sdk, '__version__', None)
    if ((sdk_version is None) or
            (sdk_version and
             (parse_version(sdk_version) < parse_version('17.1')))):
        # It allows the __version__ to be '' as that value is used in development builds
        raise ImportError
    from avi.sdk.utils.ansible_utils import avi_ansible_api
    HAS_AVI = True
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        se_obj=dict(type='dict', ),
        se_csp_vnics=dict(type='list', ),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=False)
    se_obj = module.params['se_obj']
    se_csp_vnics = module.params['se_csp_vnics']
    for d_vnic in se_obj['data_vnics']:
        nic_id = int(d_vnic['linux_name'].replace('eth', ''))
        nic_conf = [obj for obj in se_csp_vnics if obj['nic'] == nic_id]
        ipv4_addrs = nic_conf[0].get('ipv4_addrs', None)
        ipv6_addrs = nic_conf[0].get('ipv6_addrs', None)
        vnic_networks_lst = []
        if ipv4_addrs:
            for ipv4_addr in ipv4_addrs.split(','):
                addr, mask = ipv4_addr.split('/')
                vnic_networks = {
                    "ctlr_alloc": False,
                    "ip": {
                        "ip_addr": {
                            "addr": addr.strip(),
                            "type": "V4"
                        },
                        "mask": mask.strip()
                    },
                    "mode": "STATIC"
                }
                vnic_networks_lst.append(vnic_networks)
        if ipv6_addrs:
            for ipv6_addr in ipv6_addrs.split(','):
                addr, mask = ipv6_addr.split('/')
                vnic_networks = {
                    "ctlr_alloc": False,
                    "ip": {
                        "ip_addr": {
                            "addr": addr.strip(),
                            "type": "V6"
                        },
                        "mask": mask.strip()
                    },
                    "mode": "STATIC"
                }
                vnic_networks_lst.append(vnic_networks)
        if vnic_networks_lst:
            d_vnic['vnic_networks'] = vnic_networks_lst
        else:
            return module.exit_json(changed=False)

    module.params.update(se_obj)
    module.params.update(
        {
            'avi_api_update_method': 'put',
            'state': 'present'
        }
    )
    module.params.pop('se_obj')
    module.params.pop('se_csp_vnics')
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'serviceengine',
                           set([]))

if __name__ == '__main__':
    main()
