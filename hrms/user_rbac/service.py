from django.db import connection, transaction
from django.db.models import F, Q
from django.core.exceptions import PermissionDenied

from user_rbac.models import Modules, Relationmodule, Rolespermission
from users.models import Users, Userroles
from django.utils import timezone
class RbacService:
    TRUE_RECURSIVE_RELATION_QUERY = """
        WITH RECURSIVE parent_modules AS (
            SELECT rm.*
            FROM relationmodule rm
            WHERE rm.childmoduleid = %s

            UNION

            SELECT rm2.*
            FROM relationmodule rm2
            INNER JOIN parent_modules pm ON rm2.childmoduleid = pm.parentmoduleid
        ),
        child_modules AS (
            SELECT rm.*
            FROM relationmodule rm
            WHERE rm.parentmoduleid = %s

            UNION

            SELECT rm2.*
            FROM relationmodule rm2
            INNER JOIN child_modules cm ON rm2.parentmoduleid = cm.childmoduleid
        ),
        all_relations AS (
            SELECT * FROM parent_modules
            UNION
            SELECT * FROM child_modules
            UNION
            SELECT * FROM relationmodule 
              WHERE parentmoduleid = %s OR childmoduleid = %s
        )
        SELECT DISTINCT id FROM all_relations;
    """

    FALSE_RECURSIVE_RELATION_QUERY = """
        WITH RECURSIVE all_children AS (
            SELECT * FROM relationmodule WHERE parentmoduleid = %s

            UNION ALL

            SELECT rm.*
            FROM relationmodule rm
            INNER JOIN all_children ac ON rm.parentmoduleid = ac.childmoduleid
        )
        SELECT id FROM all_children
        UNION
        SELECT id FROM relationmodule WHERE parentmoduleid = %s;
    """
    
    def _execute_recursive_query(self, query: str, module_id: int) -> list[int]:
        """ Executes the raw recursive SQL query and returns a list of Relationmodule IDs. """
        relation_ids = []
        with connection.cursor() as cursor:
            if query == self.TRUE_RECURSIVE_RELATION_QUERY:
                cursor.execute(query, [module_id] * 4) # Pass moduleId four times
            else: # FALSE_RECURSIVE_RELATION_QUERY
                cursor.execute(query, [module_id] * 2) # Pass moduleId two times
                
            relation_ids = [row[0] for row in cursor.fetchall()]

        return list(set(relation_ids)) 

    # --- NEW: Recursive Sorting Method ---
    def _sort_modules_by_id(self, modules: list[dict]) -> list[dict]:
        """
        Recursively sorts modules and their children by ID.
        (Equivalent to NestJS's private sortModulesById method)
        """
        # 1. Sort the current level of modules by 'id'
        sorted_modules = sorted(modules, key=lambda x: x['id'])
        
        result = []
        for module in sorted_modules:
            # 2. Check and sort children recursively
            if 'children' in module and module['children']:
                sorted_children = self._sort_modules_by_id(module['children'])
                
                # Use dictionary unpacking to handle the 'children' key
                new_module = {**module, 'children': sorted_children}
            else:
                # Remove the 'children' key if it was present but empty or not present
                new_module = {k: v for k, v in module.items() if k != 'children'}

            result.append(new_module)
            
        return result

    # --- 1. assignPermissions (Write/Update Logic) ---
    @transaction.atomic
    def assign_permissions(self, role_id: int, module_id: int, is_enable: bool, current_user_id: int, organization_id: int):
        """
        Assigns or revokes permissions recursively based on module hierarchy.
        """
        
        query = self.TRUE_RECURSIVE_RELATION_QUERY if is_enable else self.FALSE_RECURSIVE_RELATION_QUERY
        relation_ids = self._execute_recursive_query(query, module_id)
        
        if not relation_ids:
            # If no relations found, return the current matrix
            return {
                "message": f"No relations found to update for Module ID {module_id}.",
                "moduleId": module_id,
                "totalUpdated": 0,
                "updatedMatrix": self.get_modules_by_role(role_id),
            }

        update_count = Rolespermission.objects.filter(
            relationid_id__in=relation_ids,
            roleid_id=role_id,
            createdby_id=organization_id
            
            
        ).update(
            isenable=is_enable,
            updateat=timezone.now(),
            updatedby_id=current_user_id
        )
        
        updated_matrix = self.get_modules_by_role(role_id)
        
        return {
            "message": f"Permissions {is_enable and 'enabled' or 'disabled'} for role",
            "moduleId": module_id,
            "totalUpdated": update_count, 
            "updatedMatrix": updated_matrix,
        }

    # --- 2. getModulesByRole (Read Logic) ---
    def get_modules_by_role(self, role_id: int) -> list[dict]:
        """
        Retrieves all enabled/disabled permissions for a role and structures them into a parent-child hierarchy.
        """
        is_super_admin = role_id == 1

        permissions_query = Rolespermission.objects.select_related(
            'relationid__parentmoduleid', 
            'relationid__childmoduleid',  
            'roleid',                     
        ).filter(isdelete=False) 

        if not is_super_admin:
            permissions_query = permissions_query.filter(roleid_id=role_id)
            
        permissions = permissions_query.order_by('relationid__parentmoduleid__id', 'relationid__childmoduleid__id')
        
        module_map = {} 
        child_to_parent_map = {}

        for perm in permissions:
            rel = perm.relationid
            parent = rel.parentmoduleid
            child = rel.childmoduleid
            is_enable = perm.isenable
            
            if not parent:
                continue

            def get_or_create_module(module_obj, is_enable_status):
                mod_id = module_obj.pk
                if mod_id not in module_map:
                    entry = {
                        'id': mod_id,
                        'name': module_obj.modulename,
                        'is_enable': is_enable_status,
                    }
                    module_map[mod_id] = entry
                elif is_enable_status:
                    module_map[mod_id]['is_enable'] = module_map[mod_id]['is_enable'] or is_enable_status
                return module_map[mod_id]

            # Parent add/update
            parent_entry = get_or_create_module(parent, is_enable)
            
            # Child add/update
            if child:
                child_entry = get_or_create_module(child, is_enable)
                child_to_parent_map[child.pk] = parent.pk

                # Force parent to true if child is true (propagation up)
                if is_enable:
                    parent_entry['is_enable'] = True
        
        # Nesting children into parents
        for child_id, parent_id in child_to_parent_map.items():
            parent_entry = module_map.get(parent_id)
            child_entry = module_map.get(child_id)
            
            if parent_entry and child_entry:
                if 'children' not in parent_entry:
                    parent_entry['children'] = []
                parent_entry['children'].append(child_entry)
        
        # Final Root Modules Extraction
        all_child_ids = set(child_to_parent_map.keys())
        roots = [mod for mod in module_map.values() if mod['id'] not in all_child_ids]
        
        # 3. Apply the recursive sorting logic (Equivalent to this.sortModulesById)
        return self._sort_modules_by_id(roots)

    # --- 3. getAllRolesPermissionMatrix (Read All Logic) ---
    def get_all_roles_permission_matrix(self):
        """
        Retrieves the permission matrix for all roles.
        """
        roles = Userroles.objects.all().filter(isdelete=False) 
        results = []

        for role in roles:
            results.append({
                'role_id': role.pk,
                'role_name': getattr(role, 'rolename', 'Unknown Role'), 
                'modules': self.get_modules_by_role(role.pk),
            })
            
        return results