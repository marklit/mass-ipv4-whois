# Mass IPv4 WHOIS Collection Tool

[![license](http://img.shields.io/badge/license-MIT-red.svg?style=flat)](http://opensource.org/licenses/MIT)

There is a [blog post](http://tech.marksblogg.com/mass-ip-whois-django-kafka.html) that accompanies this code base.

## Running this code base locally

The following allows you to run this code base locally. These commands were tested on a fresh installation of Ubuntu 14.04.3 LTS.

Various dependencies are needed, this will install them via Debian packages.

```bash
$ sudo apt-get update
$ sudo apt-get install -y \
    default-jre \
    jq \
    python-dev \
    python-pip \
    python-virtualenv \
    redis-server \
    zip \
    zookeeperd
```

The following will install and launch a known-good version of Kafka.

```
$ cd /tmp
$ curl -O http://mirror.cc.columbia.edu/pub/software/apache/kafka/0.8.2.1/kafka_2.11-0.8.2.1.tgz
$ tar -xzf kafka_2.11-0.8.2.1.tgz
$ cd kafka_2.11-0.8.2.1/
$ nohup bin/kafka-server-start.sh \
    config/server.properties \
    > ~/kafka.log 2>&1 &
$ export PATH="`pwd`/bin:$PATH"
```

The following will create the results and metrics topics in Kafka.

```bash
$ kafka-topics.sh \
    --zookeeper 127.0.0.1:2181 \
    --create \
    --partitions 1 \
    --replication-factor 1 \
    --topic results

$ kafka-topics.sh \
    --zookeeper 127.0.0.1:2181 \
    --create \
    --partitions 1 \
    --replication-factor 1 \
    --topic metrics
```

The following will launch Redis.

```bash
$ redis-server &
```

The following will create a virtual environment and install various Python-based dependencies.

```bash
$ virtualenv .ips
$ source .ips/bin/activate
$ pip install -r requirements.txt requirements-dev.txt
```

The following will bootstrap a local database.

```bash
$ cd ips
$ python manage.py migrate
```

The following will generate 4.7 million seed IP addresses that will be used by workers.

```bash
$ python manage.py gen_ips
```

Set the coordinator IP address:

```bash
$ python manage.py set_config 127.0.0.1
```

The following launches the web interface for the coordinator.

```bash
$ python manage.py runserver &
```

The following launches the look up worker, telemetry reporting and process that collects IP addresses from the coordinator.

```bash
$ python manage.py celeryd --concurrency=5 &
$ python manage.py celerybeat &
$ python manage.py get_ips_from_coordinator &
```

The following launches the process that collects the WHOIS records and stores unique CIDR blocks in Redis.

```
$ python manage.py collect_whois &
```

## Monitoring

To see aggregated telemetry:

```bash
$ python manage.py telemetry
```

If you want to monitor celery's activity run the following:

```bash
$ watch 'python manage.py celery inspect stats'
```

To see the results of successful WHOIS queries:

```bash
$ kafka-console-consumer.sh \
    --zookeeper localhost:2181 \
    --topic results \
    --from-beginning
```

To continuously dump results to a file:

```bash
$ kafka-console-consumer.sh \
    --zookeeper localhost:2181 \
    --topic results \
    --from-beginning > output &
```

To see per-minute metrics from the workers:

```bash
$ kafka-console-consumer.sh \
    --zookeeper localhost:2181 \
    --topic metrics \
    --from-beginning
```

## Deployment

To run Ansible on a cloud service you first need to create an inventory file like the following.

```bash
$ vi devops/inventory
```

```ini
[coordinator]
coord1 ansible_host=x.x.x.x ansible_user=ubuntu ansible_private_key_file=~/.ssh/ec2.pem

[worker]
worker1 ansible_host=x.x.x.x ansible_user=ubuntu ansible_private_key_file=~/.ssh/ec2.pem
worker2 ansible_host=x.x.x.x ansible_user=ubuntu ansible_private_key_file=~/.ssh/ec2.pem
worker3 ansible_host=x.x.x.x ansible_user=ubuntu ansible_private_key_file=~/.ssh/ec2.pem
```

To provision and deploy run:

```bash
$ zip -r \
    app.zip \
    ips/ *.txt \
    -x *.sqlite3 \
    -x *.pid \
    -x *.pyc

$ cd devops
$ ansible-playbook bootstrap.yml
```