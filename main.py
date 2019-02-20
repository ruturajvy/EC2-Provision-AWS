import boto3
import json
import time
ec2 = boto3.client('ec2')
resource = boto3.resource('ec2')

def prettyprint(resp_obj):
	print(json.dumps(resp_obj, indent=4, sort_keys=True))

def listimages(ec2):
	response = ec2.describe_images(Filters=[\
	{'Name': 'state', 'Values': ['available']},\
	{'Name':'architecture','Values':['x86_64']},\
	{'Name':'name','Values':['ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20181223']},])
	for image in response['Images']:
		print("Name: " + image['Name'])
		print("ImageId: " + image['ImageId'])
	return response['Images'][0]['ImageId']


def is_instance(ec2):
	custom_filter = [{
    'Name':'tag:Name', 
    'Values': ['Jenkins-Build-Server']}]
	instances = ec2.describe_instances(Filters=custom_filter)
	if len(instances['Reservations']):
		for res in instances['Reservations']:
			for ins in res['Instances']:
				instance_state = ins['State']['Name']
				if instance_state == 'running' or instance_state == 'stopping' or instance_state == 'stopped' or instance_state == 'pending':
					return True
	else:
		return False

def generate_keypair(ec2, name):
	
	allkeys = ec2.describe_key_pairs()
	for key in allkeys['KeyPairs']:
		if name.lower() == key['KeyName'].lower():
			return key['KeyName']
	ec2key = ec2.create_key_pair(KeyName = name)
	kname = ec2key['KeyName']
	with open(kname +'.pem','w') as f:
		f.write(ec2key['KeyMaterial'])
	print("Created a key-pair named: %s" % (kname))
	print("Stored the private key in %s.pem" %(kname) )

	
def create_security_group(ec2,name):
	allgroups = ec2.describe_security_groups()
	for group in allgroups['SecurityGroups']:
		if name.lower() == group['GroupName'].lower():
			return group['GroupId']
	group = ec2.create_security_group(GroupName=name,Description='Created for DevOps HW1')
	group_id = group['GroupId']
	#print('Security Group Created %s.' % (group_id))
	ec2.authorize_security_group_ingress(
	GroupId=group_id,
	IpPermissions=[
		{'IpProtocol': 'icmp',
			'FromPort': -1,
			'ToPort': -1,
			'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
		{'IpProtocol': 'tcp',
			'FromPort': 8080,
			'ToPort': 8080,
			'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
		{'IpProtocol': 'tcp',
			'FromPort': 22,
			'ToPort': 22,
			'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
	])
	return group_id
		#print('Ingress Successfully Set %s' % data)
		
def create_instance(ec2, resource,imageid,instancetype, keyname, group):
	if not is_instance(ec2):
		instance = resource.create_instances(\
		MinCount=1,\
		MaxCount=1,\
		ImageId=imageid,\
		InstanceType=instancetype,\
		KeyName=keyname,\
		SecurityGroupIds=[group],\
		TagSpecifications=[
			{
				'ResourceType': 'instance',
				'Tags': [
					{
						'Key': 'Name',
						'Value': 'Jenkins-Build-Server'
					},
				]
			},
		]
		)
		#print(instance)
		return instance[0].instance_id
	else:
		custom_filter = [{
    	'Name':'tag:Name', 
    	'Values': ['Jenkins-Build-Server']}]
		resp = ec2.describe_instances(Filters=custom_filter)
		for res in resp['Reservations']:
			for ins in res['Instances']:
				if ins['State']['Name'] == 'running' or ins['State']['Name']=='stopping' or ins['State']['Name']=='stopped' or ins['State']['Name']=='pending':
					return ins['InstanceId']

def get_instance_info(res,id1):
	#print(id1)
	instance = res.describe_instances(InstanceIds=[id1])
	ip = instance['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
	return ip
def terminate_instances(ec2,instance_list):
	response = ec2.terminate_instances(InstanceIds=instance_list)
	prettyprint(response)

key_name = generate_keypair(ec2, 'DevOps-Key')
group_id = create_security_group(ec2, 'DevOps-Group')
vm_id = create_instance(ec2,resource, listimages(ec2), 't2.micro', key_name, group_id)
time.sleep(2)
vm_ip = get_instance_info(ec2,vm_id)
print(vm_ip)
#instance_list = [vm_id]
#term = terminate_instances(ec2,instance_list)
#is_instance(ec2)