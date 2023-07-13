# Configuration file for ipcontroller.

#------------------------------------------------------------------------------
# Application(SingletonConfigurable) configuration
#------------------------------------------------------------------------------
## This is an application.

## The date format used by logging formatters for %(asctime)s
#  Default: '%Y-%m-%d %H:%M:%S'
# c.Application.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#  Default: '[%(name)s]%(highlevel)s %(message)s'
# c.Application.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#  Choices: any of [0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL']
#  Default: 30
# c.Application.log_level = 30

## Instead of starting the Application, dump configuration to stdout
#  Default: False
# c.Application.show_config = False

## Instead of starting the Application, dump configuration to stdout (as JSON)
#  Default: False
# c.Application.show_config_json = False

#------------------------------------------------------------------------------
# BaseIPythonApplication(Application) configuration
#------------------------------------------------------------------------------
## IPython: an enhanced interactive Python shell.

## Whether to create profile dir if it doesn't exist
#  Default: False
# c.BaseIPythonApplication.auto_create = False

## Whether to install the default config files into the profile dir. If a new
#  profile is being created, and IPython contains config files for that profile,
#  then they will be staged into the new directory.  Otherwise, default config
#  files will be automatically generated.
#  Default: False
# c.BaseIPythonApplication.copy_config_files = False

## Path to an extra config file to load.
#  
#  If specified, load this config file in addition to any other IPython config.
#  Default: ''
# c.BaseIPythonApplication.extra_config_file = ''

## The name of the IPython directory. This directory is used for logging
#  configuration (through profiles), history storage, etc. The default is usually
#  $HOME/.ipython. This option can also be specified through the environment
#  variable IPYTHONDIR.
#  Default: ''
# c.BaseIPythonApplication.ipython_dir = ''

## The date format used by logging formatters for %(asctime)s
#  See also: Application.log_datefmt
# c.BaseIPythonApplication.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#  See also: Application.log_format
# c.BaseIPythonApplication.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#  See also: Application.log_level
# c.BaseIPythonApplication.log_level = 30

## Whether to overwrite existing config files when copying
#  Default: False
# c.BaseIPythonApplication.overwrite = False

## The IPython profile to use.
#  Default: 'default'
# c.BaseIPythonApplication.profile = 'default'

## Instead of starting the Application, dump configuration to stdout
#  See also: Application.show_config
# c.BaseIPythonApplication.show_config = False

## Instead of starting the Application, dump configuration to stdout (as JSON)
#  See also: Application.show_config_json
# c.BaseIPythonApplication.show_config_json = False

## Create a massive crash report when IPython encounters what may be an internal
#  error.  The default is to append a short message to the usual traceback
#  Default: False
# c.BaseIPythonApplication.verbose_crash = False

#------------------------------------------------------------------------------
# BaseParallelApplication(BaseIPythonApplication) configuration
#------------------------------------------------------------------------------
## IPython: an enhanced interactive Python shell.

## Whether to create profile dir if it doesn't exist
#  See also: BaseIPythonApplication.auto_create
# c.BaseParallelApplication.auto_create = False

## whether to cleanup old logfiles before starting
#  Default: False
# c.BaseParallelApplication.clean_logs = False

## String id to add to runtime files, to prevent name collisions when using
#  multiple clusters with a single profile simultaneously.
#  
#  When set, files will be named like: 'ipcontroller-<cluster_id>-engine.json'
#  
#  Since this is text inserted into filenames, typical recommendations apply:
#  Simple character strings are ideal, and spaces are not recommended (but should
#  generally work).
#  Default: ''
# c.BaseParallelApplication.cluster_id = ''

## Whether to install the default config files into the profile dir.
#  See also: BaseIPythonApplication.copy_config_files
# c.BaseParallelApplication.copy_config_files = False

## Path to an extra config file to load.
#  See also: BaseIPythonApplication.extra_config_file
# c.BaseParallelApplication.extra_config_file = ''

## 
#  See also: BaseIPythonApplication.ipython_dir
# c.BaseParallelApplication.ipython_dir = ''

## The date format used by logging formatters for %(asctime)s
#  See also: Application.log_datefmt
# c.BaseParallelApplication.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#  See also: Application.log_format
# c.BaseParallelApplication.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#  See also: Application.log_level
# c.BaseParallelApplication.log_level = 30

## whether to log to a file
#  Default: False
# c.BaseParallelApplication.log_to_file = False

## The ZMQ URL of the iplogger to aggregate logging.
#  Default: ''
# c.BaseParallelApplication.log_url = ''

## Whether to overwrite existing config files when copying
#  See also: BaseIPythonApplication.overwrite
# c.BaseParallelApplication.overwrite = False

## The IPython profile to use.
#  See also: BaseIPythonApplication.profile
# c.BaseParallelApplication.profile = 'default'

## Instead of starting the Application, dump configuration to stdout
#  See also: Application.show_config
# c.BaseParallelApplication.show_config = False

## Instead of starting the Application, dump configuration to stdout (as JSON)
#  See also: Application.show_config_json
# c.BaseParallelApplication.show_config_json = False

## Create a massive crash report when IPython encounters what may be an
#  See also: BaseIPythonApplication.verbose_crash
# c.BaseParallelApplication.verbose_crash = False

## Set the working dir for the process.
#  Default: '/scratch/snx3000/unicore/FILESPACE/de6e5399-ec38-439d-bce8-e5543f205fbe/W_20230701165623'
# c.BaseParallelApplication.work_dir = '/scratch/snx3000/unicore/FILESPACE/de6e5399-ec38-439d-bce8-e5543f205fbe/W_20230701165623'

#------------------------------------------------------------------------------
# IPController(BaseParallelApplication) configuration
#------------------------------------------------------------------------------
## Whether to create profile dir if it doesn't exist.
#  Default: True
# c.IPController.auto_create = True

## Depth of spanning tree schedulers
#  Default: 1
# c.IPController.broadcast_scheduler_depth = 1

## whether to cleanup old logfiles before starting
#  See also: BaseParallelApplication.clean_logs
# c.IPController.clean_logs = False

## IP on which to listen for client connections. [default: loopback]
#  Default: ''
# c.IPController.client_ip = ''

## JSON filename where client connection info will be stored.
#  Default: 'ipcontroller-client.json'
# c.IPController.client_json_file = 'ipcontroller-client.json'

## Pool of ports to use for client connections
#  
#  This list will be consumed to populate the ports to be used when binding
#  controller sockets used for client connections
#  
#  Can be specified as a list or string expressing a range
#  
#  If this list is empty or exhausted, the common `ports` pool will be consumed.
#  
#  See also ports and engine_ports
#  Default: []
# c.IPController.client_ports = []

## 0MQ transport for client connections. [default : tcp]
#  Default: 'tcp'
# c.IPController.client_transport = 'tcp'

## String id to add to runtime files, to prevent name collisions when
#  See also: BaseParallelApplication.cluster_id
# c.IPController.cluster_id = ''

## DEPRECATED: use ports
#  Default: ()
# c.IPController.control = ()

## Whether to install the default config files into the profile dir.
#  See also: BaseIPythonApplication.copy_config_files
# c.IPController.copy_config_files = False

## The CurveZMQ public key for the controller.
#  
#  Engines and clients use this for the server key.
#  Default: b''
# c.IPController.curve_publickey = b''

## The CurveZMQ secret key for the controller
#  Default: b''
# c.IPController.curve_secretkey = b''

## The class to use for the DB backend
#  
#  Options include:
#  
#  SQLiteDB: SQLite MongoDB : use MongoDB DictDB  : in-memory storage (fastest,
#  but be mindful of memory growth of the Hub) NoDB    : disable database
#  altogether (default)
#  Default: <class 'ipyparallel.controller.dictdb.DictDB'>
# c.IPController.db_class = <class 'ipyparallel.controller.dictdb.DictDB'>

## Enable CurveZMQ encryption and authentication
#  
#  Caution: known to have issues on platforms with getrandom
#  Default: False
# c.IPController.enable_curve = False

## IP on which to listen for engine connections. [default: loopback]
#  Default: ''
# c.IPController.engine_ip = ''

## JSON filename where engine connection info will be stored.
#  Default: 'ipcontroller-engine.json'
# c.IPController.engine_json_file = 'ipcontroller-engine.json'

## Pool of ports to use for engine connections
#  
#  This list will be consumed to populate the ports to be used when binding
#  controller sockets used for engine connections
#  
#  Can be specified as a list or string expressing a range
#  
#  If this list is exhausted, the common `ports` pool will be consumed.
#  
#  See also ports and client_ports
#  Default: []
# c.IPController.engine_ports = []

## ssh url for engines to use when connecting to the Controller processes. It
#  should be of the form: [user@]server[:port]. The Controller's listening
#  addresses must be accessible from the ssh server
#  Default: ''
# c.IPController.engine_ssh_server = ''

## 0MQ transport for engine connections. [default: tcp]
#  Default: 'tcp'
# c.IPController.engine_transport = 'tcp'

## Path to an extra config file to load.
#  See also: BaseIPythonApplication.extra_config_file
# c.IPController.extra_config_file = ''

## DEPRECATED: use ports
#  Default: ()
# c.IPController.hb = ()

## DEPRECATED: use ports
#  Default: ()
# c.IPController.iopub = ()

## Set the controller ip for all connections.
#  Default: '127.0.0.1'
# c.IPController.ip = '127.0.0.1'

## 
#  See also: BaseIPythonApplication.ipython_dir
# c.IPController.ipython_dir = ''

## The external IP or domain name of the Controller, used for disambiguating
#  engine and client connections.
#  Default: 'nid00477'
# c.IPController.location = 'nid00477'

## The date format used by logging formatters for %(asctime)s
#  See also: Application.log_datefmt
# c.IPController.log_datefmt = '%Y-%m-%d %H:%M:%S'

## The Logging format template
#  See also: Application.log_format
# c.IPController.log_format = '[%(name)s]%(highlevel)s %(message)s'

## Set the log level by value or name.
#  See also: Application.log_level
# c.IPController.log_level = 30

## whether to log to a file
#  See also: BaseParallelApplication.log_to_file
# c.IPController.log_to_file = False

## The ZMQ URL of the iplogger to aggregate logging.
#  See also: BaseParallelApplication.log_url
# c.IPController.log_url = ''

## DEPRECATED: use ports
#  Default: 0
# c.IPController.mon_port = 0

## IP on which to listen for monitor messages. [default: loopback]
#  Default: ''
# c.IPController.monitor_ip = ''

## 0MQ transport for monitor messages. [default : tcp]
#  Default: 'tcp'
# c.IPController.monitor_transport = 'tcp'

## DEPRECATED: use ports
#  Default: ()
# c.IPController.mux = ()

## DEPRECATED: use ports
#  Default: 0
# c.IPController.notifier_port = 0

## Whether to overwrite existing config files when copying
#  See also: BaseIPythonApplication.overwrite
# c.IPController.overwrite = False

## Pool of ports to use for the controller.
#  
#  For example:
#  
#      ipcontroller --ports 10101-10120
#  
#  This list will be consumed to populate the ports to be used when binding
#  controller sockets for engines, clients, or internal connections.
#  
#  The number of sockets needed depends on scheduler depth, but is at least 14
#  (16 by default)
#  
#  If more ports than are defined here are needed, random ports will be selected.
#  
#  Can be specified as a list or string expressing a range
#  
#  See also engine_ports and client_ports
#  Default: []
# c.IPController.ports = []

## The IPython profile to use.
#  See also: BaseIPythonApplication.profile
# c.IPController.profile = 'default'

## Engine registration timeout in seconds [default:
#  max(30,10*heartmonitor.period)]
#  Default: 0
# c.IPController.registration_timeout = 0

## DEPRECATED: use ports
#  Default: 0
# c.IPController.regport = 0

## Reload engine state from JSON file
#  Default: False
# c.IPController.restore_engines = False

## Whether to reuse existing json connection files. If False, connection files
#  will be removed on a clean exit.
#  Default: False
# c.IPController.reuse_files = False

## Instead of starting the Application, dump configuration to stdout
#  See also: Application.show_config
# c.IPController.show_config = False

## Instead of starting the Application, dump configuration to stdout (as JSON)
#  See also: Application.show_config_json
# c.IPController.show_config_json = False

## ssh url for clients to use when connecting to the Controller processes. It
#  should be of the form: [user@]server[:port]. The Controller's listening
#  addresses must be accessible from the ssh server
#  Default: ''
# c.IPController.ssh_server = ''

## DEPRECATED: use ports
#  Default: ()
# c.IPController.task = ()

## Set the zmq transport for all connections.
#  Default: 'tcp'
# c.IPController.transport = 'tcp'

## Use threads instead of processes for the schedulers
#  Default: False
# c.IPController.use_threads = False

## Create a massive crash report when IPython encounters what may be an
#  See also: BaseIPythonApplication.verbose_crash
# c.IPController.verbose_crash = False

## Set the working dir for the process.
#  See also: BaseParallelApplication.work_dir
# c.IPController.work_dir = '/scratch/snx3000/unicore/FILESPACE/de6e5399-ec38-439d-bce8-e5543f205fbe/W_20230701165623'

#------------------------------------------------------------------------------
# ProfileDir(LoggingConfigurable) configuration
#------------------------------------------------------------------------------
## An object to manage the profile directory and its resources.
#  
#  The profile directory is used by all IPython applications, to manage
#  configuration, logging and security.
#  
#  This object knows how to find, create and manage these directories. This
#  should be used by any code that wants to handle profiles.

## Set the profile location directly. This overrides the logic used by the
#  `profile` option.
#  Default: ''
# c.ProfileDir.location = ''

#------------------------------------------------------------------------------
# Session(Configurable) configuration
#------------------------------------------------------------------------------
## Object for handling serialization and sending of messages.
#  
#  The Session object handles building messages and sending them with ZMQ sockets
#  or ZMQStream objects.  Objects can communicate with each other over the
#  network via Session objects, and only need to work with the dict-based IPython
#  message spec. The Session will handle serialization/deserialization, security,
#  and metadata.
#  
#  Sessions support configurable serialization via packer/unpacker traits, and
#  signing with HMAC digests via the key/keyfile traits.
#  
#  Parameters ----------
#  
#  debug : bool
#      whether to trigger extra debugging statements
#  packer/unpacker : str : 'json', 'pickle' or import_string
#      importstrings for methods to serialize message parts.  If just
#      'json' or 'pickle', predefined JSON and pickle packers will be used.
#      Otherwise, the entire importstring must be used.
#  
#      The functions must accept at least valid JSON input, and output *bytes*.
#  
#      For example, to use msgpack:
#      packer = 'msgpack.packb', unpacker='msgpack.unpackb'
#  pack/unpack : callables
#      You can also set the pack/unpack callables for serialization directly.
#  session : bytes
#      the ID of this Session object.  The default is to generate a new UUID.
#  username : unicode
#      username added to message headers.  The default is to ask the OS.
#  key : bytes
#      The key used to initialize an HMAC signature.  If unset, messages
#      will not be signed or checked.
#  keyfile : filepath
#      The file containing a key.  If this is set, `key` will be initialized
#      to the contents of the file.

## Threshold (in bytes) beyond which an object's buffer should be extracted to
#  avoid pickling.
#  Default: 1024
# c.Session.buffer_threshold = 1024

## Whether to check PID to protect against calls after fork.
#  
#  This check can be disabled if fork-safety is handled elsewhere.
#  Default: True
# c.Session.check_pid = True

## Threshold (in bytes) beyond which a buffer should be sent without copying.
#  Default: 65536
# c.Session.copy_threshold = 65536

## Debug output in the Session
#  Default: False
# c.Session.debug = False

## The maximum number of digests to remember.
#  
#  The digest history will be culled when it exceeds this value.
#  Default: 65536
# c.Session.digest_history_size = 65536

## The maximum number of items for a container to be introspected for custom
#  serialization. Containers larger than this are pickled outright.
#  Default: 64
# c.Session.item_threshold = 64

## execution key, for signing messages.
#  Default: b''
# c.Session.key = b''

## path to file containing execution key.
#  Default: ''
# c.Session.keyfile = ''

## Metadata dictionary, which serves as the default top-level metadata dict for
#  each message.
#  Default: {}
# c.Session.metadata = {}

## The name of the packer for serializing messages. Should be one of 'json',
#  'pickle', or an import name for a custom callable serializer.
#  Default: 'json'
# c.Session.packer = 'json'

## The UUID identifying this session.
#  Default: ''
# c.Session.session = ''

## The digest scheme used to construct the message signatures. Must have the form
#  'hmac-HASH'.
#  Default: 'hmac-sha256'
# c.Session.signature_scheme = 'hmac-sha256'

## The name of the unpacker for unserializing messages. Only used with custom
#  functions for `packer`.
#  Default: 'json'
# c.Session.unpacker = 'json'

## Username for the Session. Default is your system username.
#  Default: 'rsmirigl'
# c.Session.username = 'rsmirigl'

#------------------------------------------------------------------------------
# TaskScheduler(Scheduler) configuration
#------------------------------------------------------------------------------
## Python TaskScheduler object.
#  
#  This is the simplest object that supports msg_id based DAG dependencies.
#  *Only* task msg_ids are checked, not msg_ids of jobs submitted via the MUX
#  queue.

## specify the High Water Mark (HWM) for the downstream socket in the Task
#  scheduler. This is the maximum number of allowed outstanding tasks on each
#  engine.
#  
#  The default (1) means that only one task can be outstanding on each engine.
#  Setting TaskScheduler.hwm=0 means there is no limit, and the engines continue
#  to be assigned tasks while they are working, effectively hiding network
#  latency behind computation, but can result in an imbalance of work when
#  submitting many heterogenous tasks all at once.  Any positive value greater
#  than one is a compromise between the two.
#  Default: 1
# c.TaskScheduler.hwm = 1

## select the task scheduler scheme  [default: Python LRU] Options are: 'pure',
#  'lru', 'plainrandom', 'weighted', 'twobin','leastload'
#  Choices: any of ['leastload', 'pure', 'lru', 'plainrandom', 'weighted', 'twobin']
#  Default: 'leastload'
# c.TaskScheduler.scheme_name = 'leastload'

#------------------------------------------------------------------------------
# HeartMonitor(LoggingConfigurable) configuration
#------------------------------------------------------------------------------
## A basic HeartMonitor class ping_stream: a PUB stream pong_stream: an ROUTER
#  stream period: the period of the heartbeat in milliseconds

## Whether to include every heartbeat in debugging output.
#  
#  Has to be set explicitly, because there will be *a lot* of output.
#  Default: False
# c.HeartMonitor.debug = False

## Allowed consecutive missed pings from controller Hub to engine before
#  unregistering.
#  Default: 10
# c.HeartMonitor.max_heartmonitor_misses = 10

## The frequency at which the Hub pings the engines for heartbeats (in ms)
#  Default: 3000
# c.HeartMonitor.period = 3000

#------------------------------------------------------------------------------
# DictDB(BaseDB) configuration
#------------------------------------------------------------------------------
## Basic in-memory dict-based object for saving Task Records.
#  
#  This is the first object to present the DB interface for logging tasks out of
#  memory.
#  
#  The interface is based on MongoDB, so adding a MongoDB backend should be
#  straightforward.

## The fraction by which the db should culled when one of the limits is exceeded
#  
#  In general, the db size will spend most of its time with a size in the range:
#  
#  [limit * (1-cull_fraction), limit]
#  
#  for each of size_limit and record_limit.
#  Default: 0.1
# c.DictDB.cull_fraction = 0.1

## The maximum number of records in the db
#  
#  When the history exceeds this size, the first record_limit * cull_fraction
#  records will be culled.
#  Default: 1024
# c.DictDB.record_limit = 1024

## The maximum total size (in bytes) of the buffers stored in the db
#  
#  When the db exceeds this size, the oldest records will be culled until the
#  total size is under size_limit * (1-cull_fraction). default: 1 GB
#  Default: 1073741824
# c.DictDB.size_limit = 1073741824

#------------------------------------------------------------------------------
# SQLiteDB(BaseDB) configuration
#------------------------------------------------------------------------------
## SQLite3 TaskRecord backend.

## The filename of the sqlite task database. [default: 'tasks.db']
#  Default: 'tasks.db'
# c.SQLiteDB.filename = 'tasks.db'

## The directory containing the sqlite task database.  The default is to use the
#  cluster_dir location.
#  Default: ''
# c.SQLiteDB.location = ''

## The SQLite Table to use for storing tasks for this session. If unspecified, a
#  new table will be created with the Hub's IDENT.  Specifying the table will
#  result in tasks from previous sessions being available via Clients' db_query
#  and get_result methods.
#  Default: 'ipython-tasks'
# c.SQLiteDB.table = 'ipython-tasks'
