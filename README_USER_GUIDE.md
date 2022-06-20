# User Guide : Ansible Roles for Upgrades

## Get started

This project uses Python 3.8.

1. Create a virtualenv using the Python [venv module](https://docs.python.org/3/library/venv.html) or [pew](https://github.com/berdario/pew) or [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) or your favorite virtaulenv manager:

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

2. Now install all dependencies:

```
pip install -r requirements.txt
```

which will install dependencies from `requirements.txt`.

```
Installing sshpass package:
apt-get install -y sshpass
```

3. To deactivate the virtualenv:

```
# Using venv
deactivate
```

```
# Using pew
exit
```

## Prerequisites for running playbooks

Follow the Ansible doc [pip-tools](https://github.com/jazzband/pip-tools) to install and configure Ansible playbooks for each OS type.

### Project requirements

This project uses requirements files and [pip-tools](https://github.com/jazzband/pip-tools) to help manage Python dependencies.

- `requirements.txt`: The main set of requirements for installing application-specific dependent packages.

## Run Ansible playbooks

```
ansible-playbook -i hosts site.yml -e 'username=admin password=admin client-id=hcc audience=support'
```

## Troubleshooting

#### Curl examples for token:
- To access and obtain the JWT token:
```
curl -k --location --request POST 'https://{storage_mvip}/auth/connect/token'
   --form 'client_id=client_id' --form 'grant_type=password' --form 'username=username' --form 'password=password'
```   
- To obtain the JSON Web Key Set:
```
curl -k --location --request GET 'https://{storage_mvip}/auth/.well-known/openid-configuration/jwks'
```

#### Track task progress:
- Fetch `task-id` from log.
- Run the Swagger API (`https://{mnode_ip}/task-monitor/1/`).
- Authenticate auth manually by selecting the lock present at the right side of any available API endpoint with username, password, and client-id.
- Execute the `GET /tasks/{taskId}`` endpoint with the taskID obtained from the logs to view the percentageComplete value.

Example of a successful response:
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

## Caveats

- If there is an ongoing node upgrade, the node upgrade fails with 409. However, this should not abort the playbook.
- Attempting to upgrade compute nodes already running the firmware versions included in the package (i.e compute firmware bundle) will result in the compute nodes going through the upgrade stages and subsequently report a successful upgrades for the playbook. The compute nodes will be placed into maintenance mode and rebooted to apply compute firmware bundle, even though the actual component-level firmware upgrades stage will be skipped.
- In certain setups, reducing the health check retries causes flakiness.
- If facing squid proxy error or if the mnode environment is unreachable via playbook, run the following commands to unset proxies:
    ```
    unset https_proxy
    export https_proxy=""
    ```

## General Ansible and hosts configuration details

#### Hosts configurations can be updated in the `hosts` file.
- Set the mnode ip under the `all` block.
- Set shh credentials under `all:vars` block.
- `ansible_user`
- `ansible_ssh_pass`

#### Ansible general configurations can be updated in the `ansible.cfg` file.
- This file holds all the Ansible generic configuration, which is not specific to the environment, but specific to instance. Here are some of the configurations that are set to default values in `ansible.cfg`.
- Do not change no_log to true as it enables display of all API logs, which includes environment details such as password.
- stdout_callback set to debug.
- python and ansible python interpreters set to python interpreters been used.
- deprecation_warnings set to false.

## Extended arguments for running playbook

Extended arguments can be provided while running the playbook as [JSON string format](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#defining-variables-at-runtime) or as key=value format for example:
```
ansible-playbook -i hosts site.yml -vvv -e 'username=username password=password client-id=client-id audience=audience'
```
**-v | -vv | -vvv | -vvvv | -vvvvv**

Flag to set the Ansible output verbosity level from 1-5.

**-e**

Flag to provide a list of extended arguments.

#### Alternatively, the user-specific values can be populated in the `all.yml` file. Here, is a list of required arguments:
- client_id: This is client ID which is the token server recognizes.
- mnode_ip: The management node IP.
- username and password: This is the administrator privileged cluster credentials, also used to check user grants.

#### Authorization-related configuration details:
- grant_type: Value defaulted to password, do not change this value unless the grant_type has been setup differently.
- audience: The audience value which for each client.
- clock_skew_leeway: Default value set to 30, this is the leeway specified for claim verification. Do not change this values unless this configuration has been set up differently.
- algorithms: Default value set to RS256,algorithm used for claims validation.
- auth_jwks: JWKS token response data, which is later parsed to check admin access, do not change this value.
- auth_token: Token value obtained from parsing JWT URL response data parsing, do not change this value.
- token_retries: Allowed number of retries for hitting token URL before failing.
- token_intervals: Interval of time between accessing token URLs.

#### Package related details:
- package_name: Specify the name of package before attempting an upgrade.
- version: Specify the version of the package before attempting an upgrade.

#### When performing a single node upgrade, it is necessary to update these values:
- controller_id: The cluster controller id
- hardware_ids: List of hardware ids. Example: hardware_ids: ["abcd", "def"]

#### Allowed upgrade options:
- maintenance_mode: Advised to put a node in maintenance mode before upgrade, do not change this to false unless required. Default value is true.
- force_upgrade: Forcible node upgrade, do not change this unless required. Default value is false.
- upgrade_interval: Interval of time between attempting upgrade retries.
- upgrade_retries: Allowed number of retries for performing an upgrade.
- ignore_upgrade_node_failures: Skip node failures and do not abort playbook.

#### Currently, hardware upgrade will take around 60 min, but for the safe side, we are retying around 120 min, total time = 120 * 60 = 7200 sec = 120 min = 2 hours
- retries_limit: 120
- interval: 60

#### SSL Verification os turned off at the moment.
- sf_validate_certs: Defaulted to false, do not change this unless required.

#### Compute cluster inputs:
- vcenter_ip: The is the vcenter ip, can be obtained from the asset database.
- cluster_id: This is the vcenter cluster id visible at the cluster config level or can be obtained from asset database.
- When performing a cluster upgrade, provide `vcenter_ip` and `cluster_id` only.
- Do not set `controller_id` and `hardware_ids` through extended argument.
- Ensure that no values are specified for `controller_id` and `hardware_ids` in `all.yml`.
- When performing single-node upgrade, provide `controller_id` and `hardware_ids` only.
- Do not set `vcenter_ip` and `cluster_id` through extended argument.
- Ensure that no values are specified for `vcenter_ip` and `cluster_id` in `all.yml`.

#### Cluster Health Check retires and interval limit. Please do not change this value unless required.
- cluster_hc_retries: 30
- cluster_hc_intervals: 10

## Playbook logs, messages, and recap

The standard output looks similar to the following:

```
PLAY [Hello World] *************************************************************

TASK [Say hello] ***************************************************************
ok: [127.0.0.1] => {
    "msg": "Hello, world!"
}

PLAY RECAP *********************************************************************
127.0.0.1                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
- Each task executes distinctly and can be read in the log messages.
- The collective information of the playbook result can be found in the `PLAY RECAP`.
- The Ansible `PLAY RECAP rescued` value is the count of nodes which failed upgrades, but were eventually rescued from aborting the playbook.
- The Ansible `PLAY RECAP failed` value if found displays the failed list of hardware nodes and/or the failed health checks details at the end of execution of the playbook.

## License

GNU v3

## Author Information

NetApp https://www.netapp.com
