2. Edit the ``/etc/gyan/gyan.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://gyan:GYAN_DBPASS@controller/gyan
