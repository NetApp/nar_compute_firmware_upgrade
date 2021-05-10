# Role name
nar_compute_nodes_firmware_upgrades

# Description
For H-series compute nodes, NetApp provides the **nar_compute_nodes_firmware_upgrades** Ansible role that helps you automate firmware upgrade for hardware components, such as the BMC, BIOS, and NIC.

**Note**: The Ansible role for upgrades works only on NetApp HCI H-series compute nodes. You cannot use this role to upgrade third-party compute nodes.

## Requirements

- *Compute drivers*: You have upgraded your compute node drivers. If compute node drivers are not compatible with the new firmware, the upgrade will not start. See the [Interoperability Matrix Tool](https://mysupport.netapp.com/matrix) for driver and firmware compatibility information, and check the latest [Compute Node Firmware Release Notes](https://docs.netapp.com/us-en/hci/docs/rn_relatedrn.html#compute-firmware) for important late-breaking firmware and driver details.
- *Admin privileges*: You have cluster administrator permissions to perform the upgrade.
- *Management node version*: You have management services version 2.15.28 or later.
- *DHCP-configured nodes*: If your nodes use DHCP-assigned IPv4 addresses, you should contact NetApp Support to manually update the IP addresses. This is to resolve the issue of script failures because of stale BMC IP addresses leading to nodes being unreachable.
- *Ansible*: You have [installed Ansible 2.9 or later](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installation-guide) and have familiarized yourself with [Ansible roles](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html).
- *Minimum BMC and BIOS versions*: The node you intend to upgrade meets the following minimum requirements:

| Model | Minimum BMC version | Minimum BIOS version |
| ----- | ------------------- | -------------------- |
| H300E, H500E, H700E | 6.84.00 | NA2.1
| H410C | All versions supported (no upgrade required) | All versions supported (no upgrade required) |
| H610C | 3.96.07 | 3B01 |
| H615C | 4.68.07 | 3B08.CO |

**Note**: For a complete matrix of firmware and driver firmware for your hardware, see [this KB article (login required)](https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Firmware_and_driver_versions_in_NetApp_HCI_and_NetApp_Element_software).
- *Attached media*: Disconnect any physical USB or ISO before starting a compute node upgrade.
- *KVM ESXi console*: Close all open Serial-Over-LAN (SOL) sessions and active KVM sessions in the BMC UI before starting a compute node upgrade.
- *Witness Node requirements*: In two- and three-node storage clusters, one [Witness Node](https://docs.netapp.com/us-en/hci/docs/concept_hci_nodes.html#witness-nodes) should be running in the NetApp HCI installation at all times.
- *Hardware tag requirements*: You have [added the hardware tag](https://docs.netapp.com/us-en/hci/docs/task_mnode_add_assets.html) for the compute nodes to the base asset configuration.

## Steps

1. Download the compute firmware package from the [NetApp Support Site](https://mysupport.netapp.com/site/products/all/details/netapp-hci/downloads-tab/download/62542/Compute_Firmware_Bundle).
**Note**: You should extract the TAR.GZ file to a TAR file, and then extract the TAR file to the ISO.
2. Upload the compute firmware upgrade package to the management node. You can do this by using the NetApp Hybrid Cloud Control UI or REST APIs.
3. **(If your management node has external connectivity)** Obtain the `"packageName"` and `"packageVersion"`, which you will need in a later step:
   1. Verify the repository connection:
      1. Open the package service REST API UI on the management node: `https://[management node IP]/package-repository/1/`
      2. Select **Authorize** and enter the cluster user name and password, client ID (`mnode-client`).
      3. Select **Authorize** to begin a session.
      4. Close the authorization window.
      5. From the REST API UI, select **GET ​/packages​/remote-repository​/connection**.
      6. Select **Try it out**.
      7. Select **Execute**.
     If code 200 is returned, go to the next step. If there is no connection to the remote repository, establish the connection or use the steps for the dark site option.
   2. Find the upgrade package ID:
      1. From the REST API UI, select **GET /packages**.
      2. Select **Try it out**.
      3. Select **Execute**.
      4. From the response, copy and save the upgrade package name (`"packageName"`) and package version (`"packageVersion"`) for use in a later step.
4. **(If your management node is within a dark site)** Obtain the `"packageName"` and `"packageVersion"`, which you will need in a later step.
   1. Download the latest compute node firmware image from the [NetApp Support Site](https://mysupport.netapp.com/site/products/all/details/netapp-hci/downloads-tab/download/62542/Compute_Firmware_Bundle) to a device that is accessible to the management node.
   **Note**: For dark site upgrades, you can reduce upload time if the upgrade package and the management node are both local.
   2. Upload the compute firmware upgrade package to the management node:
     1. Open the management node REST API UI on the management node: `https://[management node IP]/package-repository/1/`
     2. Select **Authorize** and enter the cluster user name and password, the client ID (`mnode-client`).
     3. Select **Authorize** to begin a session.
     4. Close the authorization window.
     5. From the REST API UI, select **POST /packages**.
     6. Select **Try it out**.
     7. Select **Browse** and select the upgrade package.
     8. Select **Execute** to initiate the upload.
     9. From the response, copy and save the package ID (`"id"`) for use in a later step.
   3. Verify the status of the upload.
     1. From the REST API UI, select **GET​ /packages​/{id}​/status**.
     2. Select **Try it out**.
     3. Enter the package ID you copied in the previous step in **id**.
     4. Select **Execute** to initiate the status request. The response indicates `state` as `SUCCESS` when complete.
     5. From the response, copy and save the upgrade package name (`"name"`) and package version (`"version"`) for use in a later step.
5. Locate the compute controller ID and hardware ID for the node you intend to upgrade:
   1. Access the REST API UI for management services by entering the management node IP address followed by `/mnode/1`: `https://[management node IP]/mnode/1/`
   2. Select **Authorize** and enter the cluster user name and password, and the client ID.
   3. Select **Authorize** to begin a session.
   4. Close the authorization window.
   5. From the REST API UI, select **GET /assets**.
   6. Select **Try it out**.
   7. Select **Execute**.
   8. From the response, copy and save the controller ID (`"id"`) and hardware ID (`"id"`) for use in a later step. Additionally, for cluster-level upgrades, you should also copy the vCenter IP address from `"ip"` under "controller":
```
"controller": [
   {
     "_links": {
       "collection": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f/controllers",
       "parent": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f",
       "root": "https://10.117.224.82/mnode/assets",
       "self": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f/controllers/aceb935f-2f54-4339-801b-2eabaff9a200"
     },
     "config": {},
     "credentialid": "6d1bce10-d46e-49b8-8a3e-cd97ede00961",
     "host_name": "",
     "id": "aceb935f-2f54-4339-801b-2eabaff9a200",
     "ip": "10.117.224.52",
     "parent": "c5c8669c-3194-4e22-8912-ce867a5d781f",
     "type": "vCenter"
   }
 ]
```
```
"hardware": [
   {
     "_links": {
       "collection": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f/hardware-nodes",
       "parent": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f",
       "root": "https://10.117.224.82/mnode/assets",
       "self": "https://10.117.224.82/mnode/assets/c5c8669c-3194-4e22-8912-ce867a5d781f/hardware-nodes/6f8d01bf-1e43-499a-ae79-42330c4b43a0"
     },
     "config": {},
     "credentialid": "8e607621-bf48-4f4e-a252-1e69f65d971e",
     "hardware_tag": "6ec5afb0-b3d2-11e8-8f84-d8c497b5d970",
     "host_name": "bmc-host_10.117.2.173",
     "id": "6f8d01bf-1e43-499a-ae79-42330c4b43a0",
     "ip": "10.117.2.173",
     "parent": "c5c8669c-3194-4e22-8912-ce867a5d781f",
     "type": "BMC"
   }
```
6. **(Cluster-level upgrade only)** Locate the cluster ID for the cluster you intend to upgrade:
   1. Access the REST API UI for management services by entering the management node IP address followed by `/vcenter/1/`: `https://[management node IP]/vcenter/1/`
   2. Select **Authorize** or any lock icon and enter the cluster user name and password, and the client ID as `mnode-client`.
   3. Select **Authorize** to begin a session.
   4. Close the window.
   5. Select **GET /vcenter/1/compute/{controller_id}**.
   6. Select **Try it out**.
   7. Enter the controller ID you copied in the previous step in the `controller_id` parameter.
   8. Select **Execute**.
   9. Copy and save the response value for `"clusterId"` under `"clusters"`.
```
"clusters": [
   {
     "clusterId": "domain-c7",
     "clusterName": "NetApp-HCI-Cluster-01",
     "clusterOid": "vim.ClusterComputeResource:domain-c7",
     "configurationEx": {
       "default_dpm_behavior": "automated",
       "default_vm_behavior": "fullyAutomated",
       "enable_vm_behavior_overrides": true,
       "hb_datastore_candidate_policy": "allFeasibleDs",
       "host_monitoring": "enabled",
       "host_power_action_rate": 3,
       "vm_component_protecting": "disabled",
       "vm_monitoring": "vmMonitoringOnly",
       "vmotion_rate": 3
     },
```
7. Download the [nar_compute_nodes_firmware_upgrades](https://github.com/NetApp/ansible) role provided by NetApp to your local machine.
**Note**: You can also manually install the role by copying it from the [NetApp GitHub repository](https://github.com/NetApp/ansible) and placing the role in the `~/.ansible/roles` directory.
8. Specify the SSH credentials and environment details in the [inventory file](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html), which is located in `etc/ansible/hosts`.
9. Specify the following variables in the `group_vars/all.yml` file. This is where you will enter the values that you copied in the previous steps.
* `mnode_ip`
* `username`
* `password`
* `package_name`
* `version`
* `controller_id` (required only for single-node upgrade)
* `hardware_id` (required only for single-node upgrade)
* `cluster_id` (required only for cluster-level upgrade)
* `vcenter_ip` (required only for cluster-level upgrade)
10. Update the `hosts` inventory file with the server/inventory details, such as IP addresses, username, and password.
**Note**: You should define the hosts in the inventory file by using IP addresses (and not fully qualified domain names [FQDNs]). The upgrade will fail if you define the hosts by using FQDNs.
11. Create the playbook to use for upgrades. If you already have a playbook and want to use that, ensure that you specify the **nar_compute_nodes_firmware_upgrades** role in this playbook.
12. Run the playbook:
```
ansible-playbook -i hosts site.yml -e 'username=username password=password client-id=client-id audience=mnode_api'
```
13. After the upgrade is complete, verify the BMC, BIOS, and NIC versions:
   1. Open a web browser and browse to the IP address of the management node.
   2.	Log in to NetApp Hybrid Cloud Control by providing the storage cluster administrator credentials.
   3.	In the top bar, select **Upgrade**, then select **COMPUTE FIRMWARE**, then expand the appropriate   cluster and select the latest package to view the current version.
