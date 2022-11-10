# Maquette Apps

A simple application development server to develop and run (web-)apps.

## Run Server

```
$ docker build 

$ docker create network mq-apps

$ docker run \
  -d \
  --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -p 9042:80 \
  --name mq-apps \
  --network mq-apps \
  mq-apps:0.0.1
```

## Manifests

```yml
applications:
- name: some-app--{{ environment }}
  buildback: static-webapp
  env:
    SOME_VARIABLE: foo bar
  command: ls -al
  services:
    - instance_ABC
    - instance_DEF
services:
- name: instance-abc
  service: postgresql
  settings:
    foo: bar
```

A manifest may contain applications and/ or service definitions. If no manifest file exists, the manifest file will be auto-detected. Variables can be defined in a YAML file. By default, if a `vars.yml` file exists, it will be used to replace values in the manifest file.

```
environment: dev
foo: bar
complex:
    variable: value
```

