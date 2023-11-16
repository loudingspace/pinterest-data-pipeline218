# pinterest-data-pipeline218

Pinterest crunches billions of data points every day to decide how to provide more value to their users. In this project, we are creating a similar system using the AWS Cloud.

## Initial explorations

We modified the supplied `user_posting_emulation.py` script by writing the contents to a file. To do this we needed to force the json to output information in strings only, as datetimes are used in two of the three tables that are used.

These are:

- `pinterest_data` data about posts updated to Pinterest

```yaml
{
  "index": 7528,
  "unique_id": "fbe53c66-3442-4773-b19e-d3ec6f54dddf",
  "title": "No Title Data Available",
  "description": "No description available Story format",
  "poster_name": "User Info Error",
  "follower_count": "User Info Error",
  "tag_list": "N,o, ,T,a,g,s, ,A,v,a,i,l,a,b,l,e",
  "is_image_or_video": "multi-video(story page format)",
  "image_src": "Image src error.",
  "downloaded": 0,
  "save_location": "Local save in /data/mens-fashion",
  "category": "mens-fashion",
}
```

- `geolocation_data` data about the location of each post

```yaml
{
  "ind": 7528,
  "timestamp": "2020-08-28 03:52:47",
  "latitude": -89.9787,
  "longitude": -173.293,
  "country": "Albania",
}
```

- `user_data` data about the user that updates the post.

```yaml
{
  "ind": 7528,
  "first_name": "Abigail",
  "last_name": "Ali",
  "age": 20,
  "date_joined": "2015-10-24 11:23:51",
}
```

We note the index number is `ind` in geo and user but `index` in pin.

## AWS

Using a supplied IAM username and password, we logged in to AWS. A .pem key file was created to allow us to connect to a preinstalled ec2 instance.

## Kafka

We installed Kafka on the ec2 instance. This required the installation of java on the Amazon Linux instance and the downloading of Kafka 2.12-2.8.1, as this is needed for the presupplied cluster.

We installed the latest version of the IAM MSK authentication package from https://github.com/aws/aws-msk-iam-auth and installed this in the lib directory of the Kafka installation. The trust policy for our ec2 client was edited using the IAM console, and then the arn for the role we had created was included in the client.properties file that is located in the bin directory.

Three Kafka topics were created using the following template:

    ./kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER_STRING --command-config client.properties --create --topic $MY_AWS_USERNAME.pin

These are the 3 topics that were created:

    - 0af8d0adfd13.geo
    - 0af8d0adfd13.pin
    - 0af8d0adfd13.user

This was verified by running

    ./kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER_STRING --command-config client.properties --list

We created a connection from the MSK cluster to an S3 bucket by first creating a customer plugin in MSK Connect. We downloaded and copied the Confluent.io Amazon S3 connector and copied it into our S3 bucket, and then created the custom plugin using the name <userid>-plugin. We then created a connector, using our <userid>-ec-access-role for authentication to the cluster, and the following connector configuration:

```
connector.class=io.confluent.connect.s3.S3SinkConnector
s3.region=us-east-1
flush.size=1
schema.compatibility=NONE
tasks.max=3
topics.regex=<userid>.*
format.class=io.confluent.connect.s3.format.json.JsonFormat
partitioner.class=io.confluent.connect.storage.partitioner.DefaultPartitioner
value.converter.schemas.enable=false
value.converter=org.apache.kafka.connect.json.JsonConverter
storage.class=io.confluent.connect.s3.storage.S3Storage
key.converter=org.apache.kafka.connect.storage.StringConverter
s3.bucket.name=user-<userid></userid>-bucket
```

### Batch processing: configuring an API in API Gateway

In API Gateway, we create a `/{proxy+}` resource. CORS was enabled and a HTTP method was then added. We supplied as the Endpoint URL the PublicDNS from our ec2 instance. The API was then deployed using Invoke URL, which we stored for use later in our pipeline. Of note is that we must specify the endpoint using `http` and not `https`, even though it defaults to https when copying from AWS (this was the cause of much debugging!) The endpoint will be the main means of communicating with our kafka rest proxy and takes the form `http://KafkaClientEC2InstancePublicDNS:8082/{proxy}`

We then installed the Confluent package for the Kafka REST Proxy on our ec2 instance. For this we modified the `kafka-rest.properties` file by adding `bootstrap.servers` and `zookeeper.connect` variables. As we had already installed the `aws-msk-iam-auth` in our $CLASSPATH we had no need to this again, but we added the following to the file, where `client` was used:

```
# Sets up TLS for encryption and SASL for authN.
client.security.protocol = SASL_SSL

# Identifies the SASL mechanism to use.
client.sasl.mechanism = AWS_MSK_IAM

# Binds SASL client implementation.
client.sasl.jaas.config = software.amazon.msk.auth.iam.IAMLoginModule required awsRoleArn="Your Access Role";

# Encapsulates constructing a SigV4 signature based on extracted credentials.
# The SASL client bound by "sasl.jaas.config" invokes this class.
client.sasl.client.callback.handler.class = software.amazon.msk.auth.iam.IAMClientCallbackHandler
```

The REST proxy is started by the following:

```
./kafka-rest-start /home/ec2-user/confluent-7.2.0/etc/kafka-rest/kafka-rest.properties
```

#### Sending data to the API using Python

Using the supplied `user_posting_emulation.py` script we modified this as `user_posting_emulation_kafka.py`. The basis of communicating with the REST proxy is the following:

```
invoke_url = "https://YourAPIInvokeURL/YourDeploymentStage/topics/YourTopicName"
#To send JSON messages you need to follow this structure
payload = json.dumps({
    "records": [
        {
        #Data should be send as pairs of column_name:value, with different columns separated by commas
        "value": {"index": df["index"], "name": df["name"], "age": df["age"], "role": df["role"]}
        }
    ]
})

headers = {'Content-Type': 'application/vnd.kafka.json.v2+json'}
response = requests.request("POST", invoke_url, headers=headers, data=payload)
```

One issue of concern was that we tested sending items to the cluster, but that these did not take the form of json objects in the first instance. This necessitated rebuilding the connector and flushing the kafka topics. So for this project we need to be mindful to keep to the specified formats for data.

We incorporated the above code into the posting emulation script. The most complicated factor were `datetime` objects, which json does not handle natively. We dealt with this by writing the following function, which returned a string for any instances od datetime objects:

```
def datetime_handler(obj):
    if isinstance(obj, (datetime, date, time)):
        return str(obj)
```

And specifying the `default=datetime_handler` argument in the `json.dumps` payload after the main dictionary was sent.

We then set up three Kafka consumers, one per topic, to accept the messages that were sent to the REST proxy. These were of the format:

```
./kafka-console-consumer.sh --bootstrap-server $BOOTSTRAP_STRING --consumer.config client.properties --topic $MY_USER_NAME.geo --from-beginning --group students
```

An example output from the consumer:

```
[ec2-user@ip-172-31-47-135 bin]$ ./kafka-console-consumer.sh --bootstrap-server $BOOTSTRAP_STRING --consumer.config client.properties --topic $MY_USER_NAME.geo --from-beginning --group students
OpenJDK 64-Bit Server VM warning: If the number of processors is expected to increase from one, then you should configure the number of parallel GC threads appropriately using -XX:ParallelGCThreads=N
{"ind":7528,"timestamp":"2020-08-28 03:52:47","latitude":-89.9787,"longitude":-173.293,"country":"Albania"}
{"ind":2863,"timestamp":"2020-04-27 13:34:16","latitude":-5.34445,"longitude":-177.924,"country":"Armenia"}
{"ind":5730,"timestamp":"2021-04-19 17:37:03","latitude":-77.015,"longitude":-101.437,"country":"Colombia"}
{"ind":8304,"timestamp":"2019-09-13 04:50:29","latitude":-28.8852,"longitude":-164.87,"country":"French Guiana"}
{"ind":8731,"timestamp":"2020-07-17 04:39:09","latitude":-83.104,"longitude":-171.302,"country":"Aruba"}
{"ind":1313,"timestamp":"2018-06-26 02:39:25","latitude":77.0447,"longitude":61.9119,"country":"Maldives"}
```

This was then reflected in the S3 bucket store, where they were stored `topics/<your_UserId>.pin/partition=0/`:

<img src="./images/s3_geo_json.png" alt="Picture of the S3 store for the .geo messages" width="500px">
