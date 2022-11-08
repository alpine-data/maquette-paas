# Maquette Apps

A simple application development server to develop and run (web-)apps.

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

