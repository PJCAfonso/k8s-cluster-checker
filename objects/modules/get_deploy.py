from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_kube_config()
apps = client.AppsV1Api()

class K8sDeploy:
    def get_deployments(ns):
        try:
            if ns != 'all':
                print ("\n[INFO] Fetching {} namespace deployments data...".format(ns))
                namespace = ns
                deployments = apps.list_namespaced_deployment(namespace, timeout_seconds=10)
            else:
                print ("\n[INFO] Fetching all namespace deployments data...")
                deployments = apps.list_deployment_for_all_namespaces(timeout_seconds=10)
            return deployments
        except ApiException as e:
            print("Exception when calling AppsV1Api->read_namespaced_deployment: %s\n" % e)