# User Guide : Ansible Roles for Upgrades

## Getting Started

This project uses Python 3.8.

Create a virtualenv using the Python [venv module](https://docs.python.org/3/library/venv.html) or [pew](https://github.com/berdario/pew) or [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) or your favorite virtaulenv manager:

```
Use the following command to install pip for Python 3:
apt install python3-pip

```

```
# Using venv
python3.8 -m venv venv

# The virtualenv won't be activated by default so activate it with:
. venv/bin/activate
```

```
# Using pew
pew new -p python3.8 ansible-roles

# The virtualenv *will* be activated by default
# but manual reactivation is done with:
pew workon ansible-roles
```

```
# Using pyenv-virtualenv
pyenv virtualenv 3.8 ansible-roles
```

Now install all dependencies:

```
pip install -r requirements.txt
```

which will install dependencies from `requirements.txt`.

```
Installing sshpass package:
apt-get install -y sshpass
```

To deactivate the virtualenv:

```
# Using venv
deactivate
```

```
# Using pew
exit
```

## Prerequisites for running playbooks

Follow the ansible doc [pip-tools](https://github.com/jazzband/pip-tools) to install and configure ansible playbooks for each OS type.


### Project Requirements

This project uses requirements files and [pip-tools](https://github.com/jazzband/pip-tools) to help manage Python dependencies.

- `requirements.txt` - The main set of requirements for installing application specific dependent pacakges.

## Running ansible playboks

How to run ansible playbook?
```
ansible-playbook -i hosts site.yml -e 'username=admin password=admin client-id=hcc audience=support'
```

## TroubleShooting shorthands

#### Curl examples for token:
- To access and obtain the JWT token
curl -k --location --request POST 'https://{storage_mvip}/auth/connect/token' 
   --form 'client_id=client_id' --form 'grant_type=password' --form 'username=username' --form 'password=password'
- To obtain the JSON Web Key Set 
curl -k --location --request GET 'https://{storage_mvip}/auth/.well-known/openid-configuration/jwks'

#### Track task progress:
- Fetch task-id from log.
- Run the swagger api (https://{mnode_ip}/task-monitor/1/) to land at the swagger API page.
- Authenticate auth manually by clicking on the lock present at the right side of any available API endpoint with username,password and client-id.
- Execute the GET /tasks/{taskId} endpoint with the taskID obtained from the logs to view the percentageComplete value.

Example successful response looks like this:
```
{
  "_links": {
    "collection": "https://localhost:442/mnode-svc-task-monitor/bar",
    "self": "https://localhost:442/mnode-svc-task-monitor/bar/3fa85f64-5717-4562-b3fc-2c963f66afa6"
  },
  "percentComplete": 62,
  "resourceActions": [
    "pause",
    "cancel"
  ],
  "resourceLink": "https://localhost:442/mnode-svc-foo/bar/3fa85f64-5717-dead-b33f-2c963f66afa6",
  "serviceName": "mnode-svc-foo",
  "state": "inProgress",
  "step": "Debugging",
  "taskId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "taskName": "Code All The Things",
  "timeStarted": "2019-02-15T18:26:39.016211+00:00",
  "timeUpdated": "2019-02-15T18:45:14.027063+00:00"
}
```

## Example to run individual task
How to run an individual task?

When you execute a playbook, you can filter tasks based on tags in two ways:

--tags 

--skip-tags

For more details read [Tags](https://docs.ansible.com/ansible/2.9/user_guide/playbooks_tags.html).
Example:
```
ansible-playbook -i hosts site.yml -e 'username=username password=password client-id=client-id audience=audience' -t validate-requirements-prereqs
```

## Example to run specific task(s).

Create a yml file within ansible-roles/compute_nodes_firmware_upgrade/roles/nar_hci_compute_nodes_firmware_upgrade/tasks

Now add tasks to this file. For example:
Filename: Validate_access_token.yml

```
---
- name: Hit /about API to collect mgmt bundle version, storage virtual ip and token url
  include_tasks: collect_mnode_about_response.yml
- name: Verify Admin access
  args:
    apply:
      delegate_to: localhost
  include_tasks: verify_admin_access_token.yml
```

## Caveats

- If there is an ongoing node upgrade going on, the node upgrade fails with 409.However, this shouldnt abort playbook.
- Upgrading the same package on a node that has previously finished upgrading does not fail on upgrade.
- On certain setup reducing the health check retries causes flakiness.

- If facing squid proxy error or if the mnode environment is unreachable via playbook, run the following commands to unset proxies
    ```
    unset https_proxy
    export https_proxy=""
    ```

## General Ansible and hosts configuration details

#### Hosts configurations can be updated in the file `hosts`.
- Set the mnode ip under all block
- Set shh credentials under all:vars block
- ansible_user
- ansible_ssh_pass

#### Ansible general configurations can be updated in the file `ansible.cfg`.
- This file holds all the ansible generic configuration which is not specific to environemnt, but specific to instance.Here are some of the configurations that are set to default values in ansible.cfg.
- Do not change no_log to true as it enables display of all API logs, which includes environment details such as password.
- stdout_callback set to debug
- python and ansible python interpreters set to python interpreters been used.
- deprecation_warnings set to false

## Extended arguments for running playbook

Extended arguments can be provided while running the playbook as [JSON string format](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#defining-variables-at-runtime) or as key=value format for example:
```
ansible-playbook -i hosts site.yml -vvv -e 'username=username password=password client-id=client-id audience=audience'
```
**-v | -vv | -vvv | -vvvv | -vvvvv**

Flag to set the Ansible output verbosity level from 1-5.

**-e**

Flag to provide a list of extended arguments.

### Alternatively, 
#### The user specific values can be populated in the file `all.yml`. Here, is a list of required arguments:
- client_id: This is client ID which is the token server recognizes.
- mnode_ip: The management node IP.
- username and password: This is the administrator privileged cluster credentials, also used to check user grants.

#### Authorization related configuration details:
- grant_type: Value defaulted to password, do not change this value unless the grant_type has been setup differently.
- audience: The audience value which for each client.
- clock_skew_leeway: Default value set to 30,this is the leeway specified for claim verification. Do not change this values unless this configuration has been set up differently.
- algorithms: Default value set to RS256,algorithm used for claims validation.
- auth_jwks: JWKS token response data, which is later parsed to check admin access, do not change this value.
- auth_token: Token value obtained from parsing JWT url response data parsing, do not change this value.
- token_retries: Allowed number of retries for hitting token url before failing.
- token_intervals: Interval of time between accessing token urls.

#### Package related details:
- package_name: Specify the name of package before attempting an upgrade.
- version: Specify the version of the package before attempting an upgrade.

#### When performing a single node upgrade, it is necessary to update these values:
- controller_id: The cluster controller id 
- hardware_ids: List of hardware ids. Example: hardware_ids: ["abcd", "def"]

#### Allowed upgrade options:
- maintenance_mode: Advised to put a node in maintenance mode before upgrade, do not change this to false unless required. Default value is True.
- force_upgrade: Forcible node upgrade, do not change this unless required. Default value is false.
- upgrade_interval: Interval of time between attempting upgrade retries.
- upgrade_retries: Allowed number of retries for performing an upgrade.
- ignore_upgrade_node_failures: Skip node failures and do not abort playbook

#### Currently, hardware upgrade will take around 60 min, but for the safe side, we are retying around 120 min, total time = 120 * 60 = 7200 sec = 120 min = 2 hours
- retries_limit: 120
- interval: 60

#### SSL Verification os turned off at the moment.
- sf_validate_certs: Defaulted to false, do not change this unless required.

#### Compute cluster inputs:
- vcenter_ip: The is the vcenter ip, can be obtained from the asset database.
- cluster_id: This is the vcenter cluster id visible at the cluster config level or can be obtained from asset database.

#### Cluster Health Check retires and interval limit. Please do not change this value unless required.
- cluster_hc_retries: 30
- cluster_hc_intervals: 10

#### When performing cluster upgrade provide vcenter_ip and cluster_id only,do not set controller_id and hardware_ids through extended argument, also ensure empty values for controller_id and hardware_ids in all.yml.
#### When performing single node upgrade provide controller_id and hardware_ids only , do not set vcenter_ip and cluster_id through extended argument,also ensure empty values for vcenter_ip and cluster_id in all.yml.

## Playbook logs,messages and recap.

The following section will walk through the Nitty-gritty of playbook messages and recaps.

The standard output will look something like this:

```
PLAY [Hello World] *************************************************************

TASK [Say hello] ***************************************************************
ok: [127.0.0.1] => {
    "msg": "Hello, world!"
}

PLAY RECAP *********************************************************************
127.0.0.1                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
Each task executes distinctly and can be read in the log messages, the collective information of the playbook result can be found in the play recap.
- The ansible play recap rescued value is the count of nodes which failed upgrades but were eventually rescued from aborting the playbook.
- The ansible play recap failed value if found displays the failed list of hardware nodes and/or the failed health checks details at the end of execution of playbook.

## License

GNU v3

## Author Information

NetApp https://www.netapp.com



