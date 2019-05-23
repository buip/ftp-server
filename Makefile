######  Bash ###########
.PHONY : build view

build :
	@# "Set execute permission for main script"
	chmod +x main.py

view :
	@\less main.py

clean :
	@\rm temp*
