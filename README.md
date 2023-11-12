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

```

```
