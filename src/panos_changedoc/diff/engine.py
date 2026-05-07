from panos_changedoc.diff.objects import (
    diff_address_groups,
    diff_address_objects,
    diff_service_objects,
    diff_zones,
)
from panos_changedoc.diff.rules import diff_nat_rules, diff_security_rules


def diff_configs(before_parsed, after_parsed):
    changes = []
    changes.extend(diff_security_rules(before_parsed.security_rules, after_parsed.security_rules))
    changes.extend(diff_nat_rules(before_parsed.nat_rules, after_parsed.nat_rules))
    changes.extend(diff_address_objects(before_parsed.address_objects, after_parsed.address_objects))
    changes.extend(diff_address_groups(before_parsed.address_groups, after_parsed.address_groups))
    changes.extend(diff_service_objects(before_parsed.service_objects, after_parsed.service_objects))
    changes.extend(diff_zones(before_parsed.zones, after_parsed.zones))
    return changes
