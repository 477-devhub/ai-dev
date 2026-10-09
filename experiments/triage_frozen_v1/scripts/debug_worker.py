import faulthandler
faulthandler.dump_traceback_later(30, repeat=True)
import worker
worker.main()
