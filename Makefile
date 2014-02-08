NAME=chunkit.py
NAME_BIN=$(basename $(NAME))

all: install

install: $(NAME)
	install -m 755 $(NAME) /usr/local/bin/$(NAME_BIN)


