## Making changes to 000.yml
- Must rebuild and restart server
    - rm -rf run
    - rsconf build
    - cd run/nginx
    - bash start.sh (leave runnin in a separate terminal)
    - sudo rsc
    - *on v4* sudo rsc

## Making changes to componants (only)
- Must rebuild and re-pull
    - rsconf build
    - *on v4* sudo rsc

## What happens when you `rsconf build`?
- Calls `rsconf.pkcli.build.default_command`
    - (https://github.com/radiasoft/rsconf/blob/ae704a1eb3c4141bfa7620d0b048bb3d5eafd36b/rsconf/pkcli/build.py#L102)
- Few intermediate calls then for every host calls `build_compile` for each componant
    - (https://github.com/radiasoft/rsconf/blob/ae704a1eb3c4141bfa7620d0b048bb3d5eafd36b/rsconf/pkcli/build.py#L46)
    - Calls either (1) `internal_build_compile` or (2) `internal_build` from the componant .py script
        - (1) (https://github.com/radiasoft/rsconf/blob/ae704a1eb3c4141bfa7620d0b048bb3d5eafd36b/rsconf/component/__init__.py#L70)
        - (2) (https://github.com/radiasoft/rsconf/blob/ae704a1eb3c4141bfa7620d0b048bb3d5eafd36b/rsconf/component/__init__.py#L73)

## Quick Lookup
- self.hdb
    - full db for the host
    - self.hdb.<component-name> is the db for just the component
- self.buildt.require_component('docker')
    - creates a dependency on a component
    - and maybe then runs that component locally ??
- z.network = self.buildt.get_component('network')
    - gets the conf for a specific component
- get_component()
    - gets the literal component object so you can call its functions. Accessing it in j2_ctxt just gets the components cfg values
- require_component (see component/sirepo_jupyterhub for an example)
    - makes sure that a component is built and let’s you access it
    `require_component`
        `build_component`
            `build_compile`
                either:
                - `intenal_build_compile` and `append_write_queue`
                - `internal_build` and `build_write`

## Notes
- bkp, github_bkp & nginx (complicated) are good example componants
- Master is v3 ??
- Workers are v4-v9 ??
- Good to wrap things just so you have a control point if you need to do something (ex. save time)


## Evan leftovers
● sirepo is running at sirepo.v4.radia.run
● you can also edit run/db/000.yml and see changes that don’t require and rm run -rf
● Jupyterhub (fnl7)
    ● rm run -rf
    ● cp etc-ecarlin/jupyterhub-000.yml package_data/dev/db/000.yml.jinja
    ● bash run/nginx/start.sh
    ● rsc
    ● on v4: rsc
    ● http://127.0.0.1:8000/hub/login
● Sirepo on fnl7
    ● rm run -rf
    ● cp etc-ecarlin/jupyterhub-000.yml package_data/dev/db/000.yml.jinja
    ● bash run/nginx/start.sh
    ● rsc
    ● on v4: rsc
    ● http://sirepo.v4.radia.run:8080 (edit /etc/hosts on mac so sirepo.v4.radia.run routes to
    127.0.0.1 `127.0.0.1 localhost localhost.localdomain sirepo.v4.radia.run`)
● To build a container
    ● cd src/radiasoft/sirepo
    ● radia_run container-build (change branch in build.sh if needed, comment out runninging
    tests)
    ● docker tag "docker.io/radiasoft/sirepo:20201120.185733" "v3.radia.run:5000/radiasoft/sirepo:dev"
    ● sudo cat /root/.docker/config.json > ~/.docker/config.json
    ● docker push "v3.radia.run:5000/radiasoft/sirepo:dev"
● Monkeypatch a container
    ● When testing it can be nice to monkeypatch a container
    ● onv4
    ● docker ps # Get id of container
    ● docker exec -it $id /bin/bash
    ● make update (cd /home/vagrant/.pyenv/versions/py3/lib/python3.7/site-packages)
    ● docker commit $id v3.radia.run:5000/radiasoft/jupyterhub:dev
    ● docker rm -f $id
    ● docker ps # after a couple seconds container should start
    ● docker exec -it $new_id /bin/bash # make sure your monkeypatch is in the new container
