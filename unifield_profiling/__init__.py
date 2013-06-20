import cProfile
import logging

def profile_this(fn):
    def profiled_fn(*args, **kwargs):
        logging.getLogger('init').info("**** START PROFILING of %s ****" % fn)
        fpath = fn.__name__ + ".profile"
        prof = cProfile.Profile()
        ret = prof.runcall(fn, *args, **kwargs)
        prof.dump_stats(fpath)
        logging.getLogger('init').info("**** END PROFILING of %s : Profile dump file at %s ****" % (fn, fpath))
        return ret
    return profiled_fn
