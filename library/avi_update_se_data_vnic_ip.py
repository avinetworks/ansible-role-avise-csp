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
module: avi_update_se_data_vnic_ip
author: Chaitanya Deshpande (chaitanya.deshpande@avinetworks.com)

short_description: Module for update se data vnic ips 
requirements: [ avisdk ]
options:
    se_obj:
        description:
            - Se object from controller after SE is connected to controller.
    se_csp_vnics:
        description:
            - SE CSP vnic config with nic id and its ips.
extends_documentation_fragment:
    - avi
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
