==================
The final approach
==================

.. _here : http://boon-code.github.com/picklebuild3/

The documentation can be found here_.

History:
--------
This is my final approach on picklebuild. I have already tried 3 times to create this tool and I had versions that could be used, but this time I think there really is a chance to complete it and create a usefull new tool.

Why did I start this project? I wrote some code for some atmel avr when I suddenly realized that I want a lot of static configurations that don't have to be changed at runtime (I was about to create a library for the rfm12 transiver chip). So I started to use a *config.h* header file and simply wrote all constants in it. At first, this was perfectly usefull, but then, I wanted to use parts of my code in another project, and so I had to manually remove lines of code and add other lines. So I realized that I want a better structur of my code, so that each module has it's own *config.h* file. This was a clean way to do it, but I had different boards that had divergent hardware pin out, and I hated it to use source control and these *config.h* files together. Well one could do that, but it wasn't really nice. I didn't bother, unless I decided to write code that I wanted to share with other people. All that *config.h* headers could frighten a newcomer that just wants to download my files, push them to his hardware, and see results.

At the same time, I once would have needed the possibility to have lists with a variable count of items (f.e. a static scheduler; I once saw such a thing; You had to write a define for each task that has to be scheduled TASK_1, TASK_2, ... and if you had 2 task you simply made an empty define. That code read so ugly...). I came up with the idea, to write a python preprocessor. I did it, but it wasn't my best idea. It turned out, not to be quite usefull, because you couldn't access defines you made in your C code.

After some time, I realized, that I want a tool that could configure source code, just like the kernel configure tool. At first I implemented a very basic program that just executed a python script that kind of asked for the parameters. I used it in some minor projects, but it wasn't that easy to use, and the scripts you had to write, were a little complicated.

I tried different ways to build a better system, I came up with the idea to build a buildsystem. Since the old version used the python pickle module, I called it picklebuild. I had some good ideas, but I didn't want people to not be able to use their favourite build system. The project gathered more and more complexity and I finally had to quit it.

Recently (around July 2011), I came up with a new idea. I wanted to make the tool as simple as possible. It should only configure source codes, copy the source tree and change them in the new directory. It should be perfectly good to structure code into modules and only file in a module should share variables (= defines in C). The user of a project that uses this configure-system should be able to choose from a gui, with descriptive help text for each constant. (After manually configuring, a config file can be saved, reused, versioned by a scm, whatever you like...)

So why did I name it  picklebuild:
----------------------------------
The first version did use pickle and I wanted to build a buildsystem. I liked the name and wanted to stick to it, although I am really thinking about renaming it to pconfig. I don't know, currently I'm not even using the pickle module, but I really like it (currently I'm using the json module...).
If you have a good idea, just tell me and I rename it... maybe...

How can you use it:
-------------------
Well, you should not yet use it for big projects. It's not stable, I maybe have to change some things about the core of the program. Basic stuff should already work, but I'm not yet using a test-framework and haven't yet tested a lot myself. A bad example is included (bad because all variables are just crap, but you can see, how this system works). Untar `test-target.tar.gz`, you should now have a `test/` directory. Now you have to open a command line and start `pconfig.py` from `test/`. Use the --help flag to see all commands. If you can't figure out how to use this tool, it's not your fault. It's a rather big project and it will take some time until this program will really be useable. You can read the **Basic Concepts** section to understand, what this tool is about and how you can use it. Don't be afraid to send me an email if you have any questions or want to contribute.

Basic Concepts:
---------------
This tool is about configuration (especially regarding C code, but it should support other languages as well, if there is a need).
Let us first clarify some words I will use to describe this tool:

Module
  A module consists of a directory (has to be in the **source** path of the
  project), and all it's subdirectories, (that aren't modules itself) that
  contains a `configure_[module name].py file.

Node
  A node is one variable that can be configured to a certain value. Nodes
  always belong to a module. They are defined in the configure script of
  the module.

DependencyFrames (Frames)
  A frame is an ordenary python function, that has been declared in a
  configure script (it has to have an cfg.depends(...) decorator).
  By it's decorator it is possible to define which nodes have to be
  configured before the frame can be executed and create new nodes.

Configure scripts have to use the config object `cfg` to create nodes or
define Frames (decorator).
