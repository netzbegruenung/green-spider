

# connection timeout for website checks (seconds)
CONNECT_TIMEOUT = 5

# response timeout for website checks
READ_TIMEOUT = 10

# Git repo for our data
GREEN_DIRECTORY_REPO = 'https://github.com/netzbegruenung/green-directory.git'

# folder in that repo that holds the data
GREEN_DIRECTORY_DATA_PATH = 'data/countries/de'

# folder we use locally to clone the repo
GREEN_DIRECTORY_LOCAL_PATH = './cache/green-directory'

# IP address of the newthinking GCMS server
GCMS_IP = "91.102.13.20"

# kind name of the spider job key datastore entities
JOB_DATASTORE_KIND = 'spider-jobs'

# kind name of the spider results datastore entities
# TODO: change back to 'spider-results'
RESULTS_DATASTORE_KIND = 'spider-results-dev'
