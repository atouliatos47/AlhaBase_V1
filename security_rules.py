# security_rules.py - Firebase-style Universal Backend

class SecurityRules:
    def __init__(self):
        # Keep only the essential rules, remove the rest
        self.rules = {
            # Public read for sensors (keep this if you need it)
            "sensors": {
                "read": "true",  # Anyone can read
                "write": "auth != null"  # But only authenticated users can write
            },
            # Admin only collection (keep this for admin stuff)
            "admin": {
                "read": "auth.uid == 'admin'",
                "write": "auth.uid == 'admin'"
            }
        }
    
    def validate_read(self, collection: str, user: str = None, resource: dict = None) -> bool:
        """Firebase-style: Default to auth required, with exceptions"""
        if collection in self.rules:
            rule = self.rules[collection]["read"]
            return self._evaluate_rule(rule, user, resource)
        
        # Default for ANY unknown collection: auth required
        return user is not None
    
    def validate_write(self, collection: str, user: str = None, resource: dict = None) -> bool:
        """Firebase-style: Default to auth required, with exceptions"""
        if collection in self.rules:
            rule = self.rules[collection]["write"]
            return self._evaluate_rule(rule, user, resource)
        
        # Default for ANY unknown collection: auth required
        return user is not None
    
    def _evaluate_rule(self, rule: str, user: str, resource: dict) -> bool:
        """Evaluate a security rule"""
        # auth != null  --> user is authenticated
        if rule == "auth != null":
            return user is not None
        
        # auth == null --> user is not authenticated  
        if rule == "auth == null":
            return user is None
        
        # true --> always allow
        if rule == "true":
            return True
        
        # false --> never allow
        if rule == "false":
            return False
        
        # resource.owner == auth.uid --> user owns the resource
        if rule == "resource.owner == auth.uid":
            return resource and resource.get("owner") == user
        
        # resource.id == auth.uid --> user matches resource ID
        if rule == "resource.id == auth.uid":
            return resource and resource.get("id") == user
        
        # auth.uid == 'admin' --> user is admin
        if "auth.uid == 'admin'" in rule:
            return user == "admin"
        
        # Default: deny access
        return False

# Create global instance
security_rules = SecurityRules()