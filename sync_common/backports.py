from osv import osv


if not hasattr(osv.osv_pool, '__getitem__'):
    def __getitem__(self, model_name):
        return self.obj_pool[model_name]
    osv.osv_pool.__getitem__ = __getitem__
