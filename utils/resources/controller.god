    WATCH = "controller"
    START_CMD = "ruby /root/appscale/AppController/djinnServer.rb"
    STOP_CMD = "ruby /root/appscale/AppController/terminate.rb"
    PORTS = [17443]

    PORTS.each do |port|
      God.watch do |w|
        w.name = "appscale-#{WATCH}-#{port}"
        w.group = WATCH
        w.interval = 30.seconds # default      
        w.start = START_CMD
        w.stop = STOP_CMD
        w.start_grace = 20.seconds
        w.restart_grace = 20.seconds
        w.log = "/var/log/appscale/#{WATCH}-#{port}.log"
        w.pid_file = "/var/appscale/#{WATCH}-#{port}.pid"
    
        w.behavior(:clean_pid_file)

        w.start_if do |start|
          start.condition(:process_running) do |c|
            c.running = false
          end
        end
    
        w.restart_if do |restart|
          restart.condition(:memory_usage) do |c|
            c.above = 150.megabytes
            c.times = [3, 5] # 3 out of 5 intervals
          end
    
          restart.condition(:cpu_usage) do |c|
            c.above = 50.percent
            c.times = 5
          end
        end
    
        # lifecycle
        w.lifecycle do |on|
          on.condition(:flapping) do |c|
            c.to_state = [:start, :restart]
            c.times = 5
            c.within = 5.minute
            c.transition = :unmonitored
            c.retry_in = 10.minutes
            c.retry_times = 5
            c.retry_within = 2.hours
          end
        end

        w.env = {
                    "APPSCALE_HOME" => "/root/appscale",
        }
      end
    end
