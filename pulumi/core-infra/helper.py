import pulumi
import pulumi_aws as aws

def get_global_tags() -> dict:
    config = pulumi.Config()
    return config.get_object("globalTags") or {}

def merge_tags(resource_name: str, additional_tags: dict = None) -> dict:
    """Helper to merge global tags with resource-specific tags."""
    tags = {
        **get_global_tags(),
        "Name": resource_name
    }

    if additional_tags:
        tags.update(additional_tags)

    return tags