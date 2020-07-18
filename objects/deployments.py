from kubernetes import client, config
from kubernetes.client.rest import ApiException
import sys, os, getopt, time
from alive_progress import alive_bar
from time import sleep
import objects as k8s

start_time = time.time()
config.load_kube_config()
apps = client.AppsV1Api()

def usage():
    parser=argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""This script can be used to fetch details about deployments \
        in kube-system namespace in k8s cluster.

Before running script export KUBECONFIG file as env:

    export KUBECONFIG=/Users/dguyhasnoname/kubeconfig\n""",
        epilog="""All's well that ends well.""")
    
    parser.add_argument('-v', '--verbose', type=str, help="verbose mode. Use this flag to get kube-system namespace deployment details.")
    args=parser.parse_args()

class Deployment:
    global k8s_object, k8s_object_list, namespace
    def get_deployments():
        try:
            namespace = 'kube-system'
            deployments = apps.list_namespaced_deployment(namespace, timeout_seconds=10)
            return deployments
        except ApiException as e:
            print("Exception when calling AppsV1Api->read_namespaced_deployment: %s\n" % e)

    # print ("Fetching deployment data...")
    # with alive_bar(1, bar = 'bubbles') as bar:
    #     for i in range(1):
    #         k8s_object_list = get_deployments()
    #         bar()
    k8s_object_list = get_deployments()
    k8s_object = 'deployment'

    def check_deployment_security(v):
        headers = ['NAMESPACE', 'DEPLOYMENT', 'CONTAINER_NAME', 'PRIVILEGED_ESC', \
        'PRIVILEGED', 'READ_ONLY_FS', 'RUN_AS_NON_ROOT', 'RUNA_AS_USER']        
        data = k8s.Check.security_context(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)

    def check_deployment_health_probes(v):
        headers = ['NAMESPACE', 'DEPLOYMENT', 'CONTAINER_NAME', 'READINESS_PROPBE', 'LIVENESS_PROBE']        
        data = k8s.Check.health_probes(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)  

    def check_deployment_resources(v): 
        headers = ['NAMESPACE', 'DEPLOYMENT', 'CONTAINER_NAME', 'LIMITS', 'REQUESTS']       
        data = k8s.Check.resources(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)

    def check_deployment_strategy(v): 
        headers = ['DEPLOYMENT', 'CONTAINER_NAME', 'STRATEGY_TYPE']
        data = k8s.Check.strategy(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)

    def check_replica(v): 
        headers = ['NAMESPACE', 'DEPLOYMENT', 'REPLICA_COUNT']
        data = k8s.Check.replica(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)         

    def check_deployment_tolerations_affinity_node_selector_priority(v): 
        headers = ['NAMESPACE', 'DEPLOYMENT', 'NODE_SELECTOR', 'TOLERATIONS', 'AFFINITY', 'PRIORITY_CLASS']     
        data = k8s.Check.tolerations_affinity_node_selector_priority(k8s_object,k8s_object_list)
        k8s.Output.print_table(data,headers,v)       

def call_all(v):
    Deployment.check_deployment_security(v)
    Deployment.check_deployment_health_probes(v)
    Deployment.check_deployment_resources(v)
    Deployment.check_deployment_strategy(v)
    Deployment.check_replica(v)
    Deployment.check_deployment_tolerations_affinity_node_selector_priority(v)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "verbose"])
        if not opts:        
            call_all("")
            
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        return

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-v", "--verbose"):
            verbose= True
            call_all(verbose)
        else:
            assert False, "unhandled option"

    print(k8s.Output.GREEN + "Total time taken: " + k8s.Output.RESET + \
    "{}s".format(round((time.time() - start_time), 2)))

if __name__ == "__main__":
    main()