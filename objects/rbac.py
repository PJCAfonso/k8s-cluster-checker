import sys, time, os, getopt, argparse, re
from concurrent.futures import ThreadPoolExecutor
start_time = time.time()
from modules import logging as logger
from modules import process as k8s
from modules.get_rbac import K8sClusterRole, K8sClusterRoleBinding, \
K8sNameSpaceRole, K8sNameSpaceRoleBinding

class ClusterRBAC:
    def __init__(self,ns):
        global namespace
        self.ns = ns
        if not ns:
            ns = 'all'
        namespace = ns

        # pulling rbac data in threads for fast execution
        global cluster_role_list, cluster_role_binding_list, ns_role_list, \
        ns_role_binding_list, _logger
        _logger = logger.get_logger('Namespace')
        with ThreadPoolExecutor(max_workers=5) as executor:      
            tmp_cluster_role_list = \
            executor.submit(K8sClusterRole.list_cluster_role)
            tmp_cluster_role_binding_list = \
            executor.submit(K8sClusterRoleBinding.list_cluster_role_binding)
            tmp_ns_role_list = \
            executor.submit(K8sNameSpaceRole.list_namespaced_role, ns)
            tmp_ns_role_binding_list = \
            executor.submit(K8sNameSpaceRoleBinding.list_namespaced_role_binding, ns)

        cluster_role_list = tmp_cluster_role_list.result()
        cluster_role_binding_list = tmp_cluster_role_binding_list.result()
        ns_role_list = tmp_ns_role_list.result()
        ns_role_binding_list = tmp_ns_role_binding_list.result()

    def get_rbac_count(v, l):
        headers = ['CLUSTER_ROLE', 'CLUSTER_ROLE_BINDING', 'ROLE', \
        'ROLE_BINDING']
        k8s.Output.print_table([[len(cluster_role_list.items), \
        len(cluster_role_binding_list.items), len(ns_role_list.items), \
        len(ns_role_binding_list.items)]], headers, True, l) 
       
    def get_cluster_role(v, l):
        k8s_object = "clusteroles"
        data = []
        headers = ['CLUSTER_ROLE', 'RULES', 'API_GROUPS', 'RESOURCES', 'VERBS']
        
        for item in cluster_role_list.items:
            if item.rules:
                rules = k8s.Rbac.get_rules(item.rules)            
                data.append([item.metadata.name, len(item.rules), \
                rules[0], rules[1], rules[2]])
            else:
                data.append([item.metadata.name, "-", "-", "-", "-"])
        k8s.Rbac.analyse_role(data, headers, k8s_object, 'all', l) 
        data = k8s.Output.append_hyphen(data, '-----------')
        data.append(["Total: " + str(len(cluster_role_list.items)), \
        rules[3], "-", "-", "-"])
        k8s.Output.print_table(data, headers, v, l)

    def get_cluster_role_binding(v, l): 
        data, rules_count = [], 0
        headers = ['CLUSTER_ROLE_BINDING', 'CLUSTER_ROLE', \
        'SERVICE_ACCOUNT', 'NAMESPACE']
        
        for item in cluster_role_binding_list.items:
            if item.subjects:
                for i in item.subjects:
                    data.append([item.metadata.name, item.role_ref.name, \
                    i.name, i.namespace])
            else:
                data.append([item.metadata.name, item.role_ref.name, '', ''])
        data = k8s.Output.append_hyphen(data, '-----------')
        data.append(["Total: " + str(len(cluster_role_binding_list.items)), \
        "-", "-", "-"])
        k8s.Output.print_table(data, headers, v, l)
        k8s.Output.csv_out(data, headers, 'rbac', 'cluster_role_binding', 'all')
        json_data = k8s.Output.json_out(data[:-2], '', headers, 'rbac', \
        'cluster_role_binding', 'all')
        _logger.info(json_data)          

    def get_ns_role(v, l):    
        data = []
        k8s_object = 'roles'
        headers = ['ROLE', 'NAMESPACE', 'RULES', 'API_GROUPS', 'RESOURCES', 'VERBS']
        for item in ns_role_list.items:
            if item.rules:
                rules = k8s.Rbac.get_rules(item.rules)
                data.append([item.metadata.name, item.metadata.namespace, \
                len(item.rules), rules[0], rules[1], rules[2]])
            else:
                data.append([item.metadata.name, item.metadata.namespace, \
                "-", "-", "-", "-"])
        k8s.Rbac.analyse_role(data, headers, k8s_object, namespace, l)
        data = k8s.Output.append_hyphen(data, '---------')
        data.append(["Total: " + str(len(ns_role_list.items)), \
        "-", "-", "-",  "-", "-"])          
        k8s.Output.print_table(data, headers, v, l)

    def get_ns_role_binding(v, l):      
        data = []
        headers = ['ROLE_BINDING', 'NAMESPACE', 'ROLE', 'GROUP_BINDING']
        for item in ns_role_binding_list.items:
            if item.subjects:
                subjects = ""
                for i in item.subjects:
                    if len(item.subjects) > 1:
                        subjects = subjects + i.name + '\n'
                    else:
                        subjects = i.name
                data.append([item.metadata.name, item.metadata.namespace, \
                item.role_ref.name, subjects])
            else:
                data.append([item.metadata.name, item.metadata.namespace, \
                item.role_ref.name, 'None'])
        data = k8s.Output.append_hyphen(data, '---------')
        data.append(["Total: " + str(len(ns_role_binding_list.items)), \
        "-", "-", "-"]) 
        k8s.Output.print_table(data, headers, v, l)
        k8s.Output.csv_out(data, headers, 'rbac', 'ns_role_binding', namespace)
        json_data = k8s.Output.json_out(data[:-2], '', headers, 'rbac', \
        'ns_role_binding', namespace)
        _logger.info(json_data)  

def call_all(v, ns, l):
    ClusterRBAC(ns)
    ClusterRBAC.get_rbac_count(v, l)      
    if not ns:
        ClusterRBAC.get_cluster_role(v, l)
        ClusterRBAC.get_cluster_role_binding(v, l)
    ClusterRBAC.get_ns_role(v, l)
    ClusterRBAC.get_ns_role_binding(v, l)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], \
        "hvn:l", ["help", "verbose", "namespace", "logging"])
        if not opts:        
            call_all('', '', '')
            k8s.Output.time_taken(start_time)
            sys.exit()
            
    except getopt.GetoptError as err:
        print(err)
        return
    verbose, ns, l = '', '', ''
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-n", "--namespace"):
            if not verbose: verbose = False
            ns = a
        elif o in ("-l", "--logging"):
            l = True                   
        else:
            assert False, "unhandled option"
    call_all(verbose, ns, l)
    k8s.Output.time_taken(start_time)     

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(k8s.Output.RED + "[ERROR] " + \
        k8s.Output.RESET + 'Interrupted from keyboard!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)