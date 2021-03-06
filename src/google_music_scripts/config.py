import sys
import time
from collections.abc import Mapping
from pathlib import Path

import appdirs
from loguru import logger
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from .__about__ import __author__, __title__
from .utils import DictMixin

COMMAND_ALIASES = {
	'del': 'delete',
	'delete': 'del',
	'down': 'delete',
	'download': 'down',
	'up': 'upload',
	'upload': 'up'
}

COMMAND_KEYS = {
	'del',
	'delete',
	'down',
	'download',
	'quota',
	'search',
	'up',
	'upload',
}

CONFIG_BASE_PATH = Path(appdirs.user_config_dir(__title__, __author__))

LOG_BASE_PATH = Path(appdirs.user_data_dir(__title__, __author__))
LOG_FORMAT = '<lvl>[{time:YYYY-MM-DD HH:mm:ss}]</lvl> {message}'
LOG_DEBUG_FORMAT = LOG_FORMAT

logger.level('NORMAL', no=25, color="<green>")
logger.level('INFO', no=20, color="<green><bold>")
logger.level('ACTION_FAILURE', no=15, color="<red>")
logger.level('ACTION_SUCCESS', no=15, color="<cyan>")

VERBOSITY_LOG_LEVELS = {
	0: 50,
	1: 40,
	2: 30,
	3: 25,
	4: 20,
	5: 15,
	6: 10,
	7: 5,
}


def convert_default_keys(item):
	if isinstance(item, Mapping):
		converted = item.__class__()
		for k, v in item.items():
			converted[k.lstrip('-').replace('-', '_')] = convert_default_keys(v)

		return converted
	else:
		return item


def get_defaults(command, *, username=None):
	config_defaults = read_config_file(username).get('defaults')
	defaults = DictMixin()

	if config_defaults:
		defaults.update(
			(k, v)
			for k, v in config_defaults.items()
			if k not in COMMAND_KEYS
		)

		if command in config_defaults:
			defaults.update(
				(k, v)
				for k, v in config_defaults[command[0]].items()
				if k not in COMMAND_KEYS
			)

		cmd_alias = COMMAND_ALIASES.get(command)
		if cmd_alias and cmd_alias in config_defaults:
			defaults.update(
				(k, v)
				for k, v in config_defaults[cmd_alias].items()
				if k not in COMMAND_KEYS
			)

	return convert_default_keys(defaults)


def read_config_file(username=None):
	config_path = CONFIG_BASE_PATH / (username or '') / 'google-music-scripts.toml'
	config_file = TOMLFile(config_path)

	try:
		config = config_file.read()
	except FileNotFoundError:
		config = TOMLDocument()

	write_config_file(config, username=username)

	return config


def write_config_file(config, username=None):
	config_path = CONFIG_BASE_PATH / (username or '') / 'google-music-scripts.toml'
	config_path.parent.mkdir(parents=True, exist_ok=True)
	config_path.touch()

	config_file = TOMLFile(config_path)
	config_file.write(config)


def ensure_log_dir(username=None):
	log_dir = LOG_BASE_PATH / (username or '') / 'logs'
	log_dir.mkdir(parents=True, exist_ok=True)

	return log_dir


def configure_logging(
	modifier=0,
	*,
	username=None,
	debug=False,
	log_to_stdout=True,
	log_to_file=False
):
	logger.remove()

	if debug:
		logger.enable('audio_metadata')
		logger.enable('google_music')
		logger.enable('google_music-proto')
		logger.enable('google_music_utils')

	verbosity = 3 + modifier

	if verbosity < 0:
		verbosity = 0
	elif verbosity > 7:
		verbosity = 7

	log_level = VERBOSITY_LOG_LEVELS[verbosity]

	if log_to_stdout:
		logger.add(
			sys.stdout,
			level=log_level,
			format=LOG_FORMAT,
			backtrace=False
		)

	if log_to_file:
		log_dir = ensure_log_dir(username=username)
		log_file = (log_dir / time.strftime('%Y-%m-%d_%H-%M-%S')).with_suffix('.log')

		logger.success("Logging to file: {}", log_file)

		logger.add(
			log_file,
			level=log_level,
			format=LOG_FORMAT,
			backtrace=False,
			encoding='utf8',
			newline='\n'
		)
