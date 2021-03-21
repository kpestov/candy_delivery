def collect_invalid_objects(request, serializer_cls, obj_key: str):
    invalid_objects = []
    for item in request.data.get('data'):
        serializer = serializer_cls(data=item)
        if not serializer.is_valid():
            invalid_objects.append({'id': serializer.data.get(obj_key)})
    return invalid_objects
