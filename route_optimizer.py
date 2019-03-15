#IMPORTS
from __future__ import division
import urllib
import Tkinter
from Tkinter import Button, Entry, Radiobutton, IntVar, Checkbutton
from Tkconstants import INSERT, DISABLED, NORMAL
import ScrolledText
import threading
import webbrowser

#GLOBAL VARIABLES
fixed_endpoint = False
fixed_endpoint_name = ""
routes = []
optimized_routes = []
total_routes = []
final_routes = []
previous_routes = []
tested_routes = []
waypoints = []
o_system = ""
d_system = ""
origins = []
destinations = []
final_best_route = []
initialized = False
cycles = 1
waypoint_adding_done = True
prefstr = "shortest"

def start():
    #CREATE THE WINDOW 
    global prefstr 
    window = Tkinter.Tk()
    screen_width = window.winfo_screenwidth() # width of the screen
    screen_height = window.winfo_screenheight() # height of the screen
    window.title("EvE Route Optimizer")
    window.geometry('%dx%d+%d+%d' % (680,640,(screen_width/2)-340,(screen_height/2)-320))
    window.configure(background='gray') 
    result = ScrolledText.ScrolledText(window,width=60,height=20)
    result.configure(font=("Arial Bold", 12), fg="white")
    result.configure(background='black') 
    start_field = Entry(window,width=37,font=("Arial Bold", 12))
    end_field = Entry(window,width=37,font=("Arial Bold", 12))
    fixed_end_field = Entry(window,width=37,font=("Arial Bold", 12))
    iteration_field = Entry(window,width=6,font=("Arial Bold", 12)) 
    start_field.insert(0, "Origin")
    end_field.insert(0, "Destination")
    fixed_end_field.insert(0, "Fixed End Point")  
    iteration_field.insert(0, "Cycles")  
    result.pack()
    start_field.pack()
    end_field.pack()
    fixed_end_field.pack()
    iteration_field.pack()
    fixed_end_field.configure(state=DISABLED)
    
    try:
        version_url = "https://sites.google.com/site/ustleveonline/route_optimizer_version"
        version_response = urllib.urlopen(version_url).read()
        local_version_file = open("route_optimizer_version","r")
        local_version = local_version_file.read()
        if str(local_version) != str(version_response):
            result.insert(INSERT,"\nAn update for EvE Route Optimizer is available.\n")
            result.see("end")
            webbrowser.open("https://sites.google.com/site/ustleveonline/route-optimizer", new=1, autoraise=True)
        else:
            result.insert(INSERT,"\nEvE Route Optimizer is up to date.\n")
            result.see("end")
    except:
        result.insert(INSERT,"\n"+"ERROR: Please check your internet connection!")
        result.see("end")
        
    #ADD A WAYPOINT
    def add_waypoint(Event=None): 
        global o_system
        global d_system
        global waypoint_adding_done
        
        waypoint_adding_done = False
        o_system = start_field.get()
        d_system = end_field.get()
        if (o_system != "" and d_system != "" and o_system != "Origin" and d_system != "Destination"):
            try:
                number_of_routes = len(routes)
                start_field.delete(0, 'end')
                end_field.delete(0, 'end')
                start_field.insert(0, d_system)
                create_route(False)
                if len(routes) > number_of_routes:
                    result.insert(INSERT,"\n"+"Added Route: "+o_system+" to "+d_system)
                    result.see("end")
                else:
                    result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                    result.see("end")
                waypoint_adding_done = True
            except:
                result.insert(INSERT,"\n"+"ERROR: Invalid!") 
                result.see("end")  
    
    #CREATE ROUTE USING GIVEN WAYPOINTS
    def create_route(optimizing):
        global routes
        global waypoints
        global o_system
        global d_system
        global prefstr
        
        #GET ORIGIN ID
        try:
            o_base = "https://esi.evetech.net/latest/search/?categories=solar_system&search="
            o_end = "&strict=true"
            o_url = o_base+o_system+o_end
            
            o_response = urllib.urlopen(o_url).read()
            o_split_response = o_response.split(":")
            o_id_section = o_split_response[1]
            o_id_leftbracket = o_id_section.replace('[', '')
            o_id_rightbracket = o_id_leftbracket.replace(']', '')
            o_id_final = o_id_rightbracket.replace('}', '')
        except:
            result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!") 
            result.see("end")
            
        #GET DESTINATION ID
        try:
            d_base = "https://esi.evetech.net/latest/search/?categories=solar_system&search="
            d_end = "&strict=true"
            d_url = d_base+d_system+d_end
            
            d_response = urllib.urlopen(d_url).read()
            d_split_response = d_response.split(":")
            d_id_section = d_split_response[1]
            d_id_leftbracket = d_id_section.replace('[', '')
            d_id_rightbracket = d_id_leftbracket.replace(']', '')
            d_id_final = d_id_rightbracket.replace('}', '')
        except:
            result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
            result.see("end")
            
        #GET ROUTE 
        try:
            r_base = "https://esi.evetech.net/latest/route/"
            r_end = "/?datasource=tranquility&flag="
            r_type = prefstr   
            r_slash = "/"
            r_url = r_base +o_id_final+r_slash+d_id_final+r_end+r_type  
        except:
            result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
            result.see("end")
            
        #IF THIS ROUTE IS PART OF THE ORIGINAL REQUEST, ADD IT TO THE LIST
        try:
            if optimizing == False:
                r_response = urllib.urlopen(r_url).read()                   
                routes.append(r_response)
                waypoints.append(o_system)
            else:
                r_response = urllib.urlopen(r_url).read()
                return r_response
        except:
            result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
            result.see("end")
    
    #OPTIMIZE THE ROUTE
    def optimize():
        global o_system
        global d_system
        global routes
        global waypoints
        global optimized_routes
        global previous_routes
        global tested_routes
        global total_routes
        global final_routes
        global origins
        global destinations
        global initialized
        global cycles
        global final_best_route
        global fixed_endpoint_name

        result.insert(INSERT,"\n")
        last_destination = ""
        last_route = [None] * 10000        
        best_route = [None] * 10000
        sys1 = ""
        sys2 = ""
        waypoints.append(d_system)
        
        #GET AND DISPLAY THE TOTAL ROUTE DISTANCE IN NUMBER OF JUMPS
        total_distance = 0
        for route in routes:
            split_route = route.split(",")
            total_distance += len(split_route)            
        result.insert(INSERT,"\n"+"Number of jumps: "+str(total_distance))
        result.see("end")

        if fixed_endpoint == False:
            #GET ID FOR THE ORIGIN
            split_for_origin = routes[0].split(",")
            first_origin = split_for_origin[0].split("[")[1]       
            
            #GET ID FOR THE LAST STOP
            final_route = routes[len(routes)-1]
            split_final_route = final_route.split(",")
            last_stop = split_final_route[len(split_final_route)-1].split("]")[0]
            
            try:
                #CONVERT ID TO NAME FOR ORIGIN
                first_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                first_end_url = "/?datasource=tranquility&language=en-us"
                first_final_url = first_begin_url+first_origin+first_end_url
                first_response = urllib.urlopen(first_final_url).read() 
                first_final_origin = first_response.split(":")[2].split(",")[0].replace('"',"")
                d_system = first_final_origin
                
                #CONVERT ID TO NAME FOR DESTINATION
                endpoint_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                endpoint_end_url = "/?datasource=tranquility&language=en-us"
                endpoint_final_url = endpoint_begin_url+last_stop+endpoint_end_url
                endpoint_response = urllib.urlopen(endpoint_final_url).read()
                endpoint_final_response = endpoint_response.split(":")[2].split(",")[0].replace('"',"")
                o_system = endpoint_final_response          
            except:
                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                result.see("end")
                
            #GET AND DISPLAY THE TOTAL ROUTE DISTANCE INCLUDING RETURN TO ORIGIN   
            return_route = create_route(True)       
            return_distance = len(return_route.split(","))
            result.insert(INSERT,"\n"+"Including return to origin: "+str(total_distance+return_distance)+"\n")
            result.see("end")
        else:          
            #SET DESTINATION TO THE FIXED ENDPOINT
            if fixed_endpoint_name != "" and fixed_endpoint_name != "Fixed End Point":
                try:
                    d_system = fixed_endpoint_name
                except:
                    result.insert(INSERT,"\n"+"ERROR: Invalid Fixed End Point!") 
                    result.see("end") 
                                             
            #GET THE ID FOR THE LAST STOP
            final_route = routes[len(final_routes)-1]
            split_final_route = final_route.split(",")
            last_stop = split_final_route[len(split_final_route)-1].split("]")[0]
            
            try:             
                #CONVERT ID TO NAME FOR DESTINATION
                endpoint_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                endpoint_end_url = "/?datasource=tranquility&language=en-us"
                endpoint_final_url = endpoint_begin_url+last_stop+endpoint_end_url
                endpoint_response = urllib.urlopen(endpoint_final_url).read()
                endpoint_final_response = endpoint_response.split(":")[2].split(",")[0].replace('"',"")
                o_system = endpoint_final_response 
            except:
                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                result.see("end")
         
            #GET AND DISPLAY THE TOTAL TRIP DISTANCE INCLUDING RETURN TO ORIGIN  
            return_route = create_route(True)        
            return_distance = len(return_route.split(","))        
            result.insert(INSERT,"\n"+"Including fixed end point: "+str(total_distance+return_distance)+"\n")
            result.see("end") 

        try:
            cycles = int(iteration_field.get())
        except:
            cycles = 1
        count = 0        
        while count < cycles:            
            count += 1   
            result.insert(INSERT,"\nCycle "+str(count)+":\n")
            result.see("end")          
            for route in routes:
                try:
                    #CONVERT ID TO NAME FOR ORIGIN
                    split_route = route.split(",")
                    origin = split_route[0].split("[")[1]
                    begin_url = "https://esi.evetech.net/latest/universe/systems/"
                    end_url = "/?datasource=tranquility&language=en-us"
                    final_url = begin_url+origin+end_url
                    response = urllib.urlopen(final_url).read() 
                    final_origin = response.split(":")[2].split(",")[0].replace('"',"")
                    o_system = final_origin                                                 
                except:
                    result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                    result.see("end")  
                     
                #ADD THE ORIGIN AS A DESTINATION SO IT'S NOT INCLUDED IN POTENTIAL ROUTES           
                if initialized == False:
                    destinations.append(o_system)
                    initialized = True
                    last_destination = o_system
                
                #WHEN THE ROUTE IS CHANGED, THE PREVIOUS WAYPOINT MUST BE UPDATED
                elif o_system != last_destination:
                    o_system = last_destination
                    
                #RESET THE BOOLEAN VALUES FOR ROUTE UPDATES
                optimized = False
                passed = False
                
                result.insert(INSERT,"\n"+"Finding the shortest route from "+o_system+" to another waypoint.\n")
                result.see("end")                   
                for waypoint in waypoints:
                    if o_system != waypoint and passed == False: #PREVENT ROUTING TO THE CURRENT SYSTEM
                        d_system = waypoint                                                                                     
                        potential_route = create_route(True) #CREATE A ROUTE TO GET THE LENGTH IN NUMBER OF JUMPS
                        split_pot = potential_route.split(",")
                        #FIND THE SHORTEST ROUTE FROM THE CURRENT LOCATION TO ANOTHER LOCATION IN THE LIST
                        if optimized == True:
                            split_best = best_route.split(",")
                            if d_system not in destinations and o_system not in origins and len(best_route) != 10000 and potential_route not in tested_routes:
                                result.insert(INSERT,"\nChecking route "+str(o_system)+" to "+str(d_system)+": "+str(len(split_pot))+" jumps. Best found: "+str(len(split_best))+" jumps.")
                                result.see("end")
                            if len(split_pot) < len(split_best) and d_system not in destinations and o_system not in origins:  
                                best_route = potential_route   
                                sys1 = o_system
                                sys2 = d_system 
                            elif len(split_pot) == len(split_best) and d_system not in destinations and o_system not in origins:
                                passed = True
                                optimized = False
                        else: 
                            if len(split_pot) < len(last_route) and d_system not in destinations and o_system not in origins:
                                if d_system not in destinations and o_system not in origins and len(best_route) != 10000 and potential_route not in tested_routes: 
                                    result.insert(INSERT,"\nChecking route "+str(o_system)+" to "+str(d_system)+": "+str(len(split_pot))+" jumps. Best found: "+str(len(last_route))+" jumps.")
                                    result.see("end") 
                                best_route = potential_route   
                                sys1 = o_system
                                sys2 = d_system
                                optimized = True 
                            elif len(split_pot) == len(last_route) and d_system not in destinations and o_system not in origins:
                                passed = True
                                optimized = False
                            else:
                                last_route = split_pot
                                
                #OPTIMAL ROUTE WAS FOUND
                if optimized == True:                                    
                    result.insert(INSERT,"\n\n"+"Optimized route: "+sys1+" to "+sys2+"\n")
                    result.see("end")
                    optimized_routes.append(best_route)                
                    origins.append(sys1)
                    destinations.append(sys2)
                    last_destination = sys2
                    
                #OPTIMAL ROUTE WAS NOT FOUND, SO THE NEXT WAYPOINT IN THE LIST IS USED
                elif optimized == False:
                    finished = False
                    for waypoint in waypoints:
                        if finished == False:
                            if o_system != waypoint and waypoint not in destinations: #GET THE FIRST UNUSED WAYPOINT
                                d_system = waypoint               
                                potential_route = create_route(True) 
                                if potential_route not in tested_routes: #THIS ROUTE HAS NOT YET BEEN EXAMINED 
                                    tested_routes.append(potential_route)                       
                                    optimized_routes.append(potential_route)                    
                                    result.insert(INSERT,"\n\n"+"No exceptional route found. Creating route: "+o_system+" to "+d_system+"\n")
                                    result.see("end")
                                    origins.append(o_system)
                                    destinations.append(d_system)
                                    last_destination = d_system
                                    finished = True 
                    if finished == False: #ALL POSSIBLE ROUTES HAVE BEEN EXAMINED FOR THIS WAYPOINT SO THE SHORTEST ONE IS SELECTED
                        previous_best_route = [None] * 10000
                        best_tested_route = []
                        for route in tested_routes:
                            split_route = str(route).split(",")                                            
                            origin = split_route[0].split("[")[1]
                            try: 
                                o_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                                o_end_url = "/?datasource=tranquility&language=en-us"
                                o_final_url = o_begin_url+origin+o_end_url
                                o_response = urllib.urlopen(o_final_url).read()
                                o_final_response = o_response.split(":")[2].split(",")[0].replace('"',"") 
                            except:
                                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                                result.see("end")    
                            if o_final_response == o_system: 
                                if len(previous_best_route) != 10000:
                                    result.insert(INSERT,"\n"+"Comparing potential routes for this waypoint: "+str(len(split_route))+" jumps VS "+str(len(previous_best_route))+" jumps.")
                                    result.see("end") 
                                s_destination = split_route[len(split_route)-1].split("]")[0]
                                try:                                                                                                                                                                   
                                    s_d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                                    s_d_end_url = "/?datasource=tranquility&language=en-us"
                                    s_d_final_url = s_d_begin_url+s_destination+s_d_end_url
                                    s_d_response = urllib.urlopen(s_d_final_url).read()
                                    s_d_final_response = s_d_response.split(":")[2].split(",")[0].replace('"',"") 
                                except:
                                    result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                                    result.see("end")   
                                if s_d_final_response not in destinations and len(split_route) < len(previous_best_route):                                                                                                         
                                    best_tested_route = route
                                    previous_best_route = split_route 
                                    
                        split_best_route = str(best_tested_route).split(",")                                            
                        origin = split_best_route[0].split("[")[1]
                        destination = split_best_route[len(split_best_route)-1].split("]")[0]
                        try:                                                                                                                               
                            o_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                            o_end_url = "/?datasource=tranquility&language=en-us"
                            o_final_url = o_begin_url+origin+o_end_url
                            o_response = urllib.urlopen(o_final_url).read()
                            t_o_final_response = o_response.split(":")[2].split(",")[0].replace('"',"")
                            
                            d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                            d_end_url = "/?datasource=tranquility&language=en-us"
                            d_final_url = d_begin_url+destination+d_end_url
                            d_response = urllib.urlopen(d_final_url).read()
                            t_d_final_response = d_response.split(":")[2].split(",")[0].replace('"',"") 
                        except:
                            result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                            result.see("end")                 
                        optimized_routes.append(best_tested_route)                    
                        result.insert(INSERT,"\n\n"+"All possible routes considered. Using route: "+t_o_final_response+" to "+t_d_final_response+"\n")
                        result.see("end")
                        origins.append(t_o_final_response)
                        destinations.append(t_d_final_response)
                        last_destination = t_d_final_response
                        finished = True 
                                                        
            total_routes.append(optimized_routes)          
            previous_routes = optimized_routes           
            optimized_routes = []
            origins = []
            destinations = []
            optimized = False
            initialized = False
        
        #SELECT THE BEST ROUTE FROM ALL CYCLES
        previous_best_distance = 10000   
        for route in total_routes: 
            total_route_distance = 0                      
            for r in route:
                s_r = r.split(",")
                total_route_distance += len(s_r)
            if previous_best_distance != 10000:
                result.insert(INSERT,"\n"+"Comparing optimized routes: "+str(total_route_distance)+" jumps VS "+str(previous_best_distance)+" jumps.")
                result.see("end")
            if total_route_distance < previous_best_distance:
                final_best_route = route
                previous_best_distance = total_route_distance            
                
        #DISPLAY THE OPTIMIZED ROUTE
        previous_destination = ""
        for route in final_best_route:
            split_route = str(route).split(",")
            origin = split_route[0].split("[")[1]
            destination = split_route[len(split_route)-1].split("]")[0]

            #CONVERT THE ID TO NAME FOR EACH ROUTE
            try:
                o_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                o_end_url = "/?datasource=tranquility&language=en-us"
                o_final_url = o_begin_url+origin+o_end_url
                o_response = urllib.urlopen(o_final_url).read()
                o_final_response = o_response.split(":")[2].split(",")[0].replace('"',"")
                
                d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                d_end_url = "/?datasource=tranquility&language=en-us"
                d_final_url = d_begin_url+destination+d_end_url
                d_response = urllib.urlopen(d_final_url).read()
                d_final_response = d_response.split(":")[2].split(",")[0].replace('"',"")            
                
                #SET THE CURRENT SYSTEM TO INITIALIZE ITERATION   
                if previous_destination == "":
                    previous_destination = o_final_response
                    result.insert(INSERT,"\n\n"+"New Route:"+"\n")
                    result.see("end")
                
                #SET THE CURRENT SYSTEM TO THE PREVIOUS DESTINATION
                if o_final_response == previous_destination:
                    final_routes.append(route)
                    previous_destination = d_final_response                 
                    result.insert(INSERT,"\n"+o_final_response+" to "+d_final_response)
                    result.see("end")
                else: #THIS IS FOR DEBUGGING AND SHOULD NEVER HAPPEN
                    result.insert(INSERT,"\n"+"ERROR: Out of order! "+o_final_response+":"+d_final_response) 
                    result.see("end")
            except:
                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                result.see("end")
                
        #GET AND DISPLAY THE TOTAL TRIP DISTANCE IN NUMBER OF JUMPS
        total_distance = 0
        for route in final_routes:
            split_route = route.split(",")
            total_distance += len(split_route)
        result.insert(INSERT,"\n\n"+"Number of jumps: "+str(total_distance))
        result.see("end")
        
        if fixed_endpoint == False:
            #GET THE ID FOR THE ORIGIN
            split_for_origin = final_routes[0].split(",")
            first_origin = split_for_origin[0].split("[")[1]                  
        
            #GET THE ID FOR THE LAST STOP
            final_route = final_routes[len(final_routes)-1]
            split_final_route = final_route.split(",")
            last_stop = split_final_route[len(split_final_route)-1].split("]")[0]
            
            try:
                #CONVERT ID TO NAME FOR ORIGIN
                first_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                first_end_url = "/?datasource=tranquility&language=en-us"
                first_final_url = first_begin_url+first_origin+first_end_url
                first_response = urllib.urlopen(first_final_url).read() 
                first_final_origin = first_response.split(":")[2].split(",")[0].replace('"',"")
                d_system = first_final_origin
                
                #CONVERT ID TO NAME FOR DESTINATION
                endpoint_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                endpoint_end_url = "/?datasource=tranquility&language=en-us"
                endpoint_final_url = endpoint_begin_url+last_stop+endpoint_end_url
                endpoint_response = urllib.urlopen(endpoint_final_url).read()
                endpoint_final_response = endpoint_response.split(":")[2].split(",")[0].replace('"',"")
                o_system = endpoint_final_response 
            except:
                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                result.see("end")
         
            #GET AND DISPLAY THE TOTAL TRIP DISTANCE INCLUDING RETURN TO ORIGIN  
            return_route = create_route(True)        
            return_distance = len(return_route.split(","))        
            result.insert(INSERT,"\n"+"Including return to origin: "+str(total_distance+return_distance)+"\n")
            result.see("end")             
        else:
            #SET DESTINATION TO THE FIXED ENDPOINT
            d_system = fixed_endpoint_name
                                             
            #GET THE ID FOR THE LAST STOP
            final_route = final_routes[len(final_routes)-1]
            split_final_route = final_route.split(",")
            last_stop = split_final_route[len(split_final_route)-1].split("]")[0]
            
            try:             
                #CONVERT ID TO NAME FOR DESTINATION
                endpoint_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                endpoint_end_url = "/?datasource=tranquility&language=en-us"
                endpoint_final_url = endpoint_begin_url+last_stop+endpoint_end_url
                endpoint_response = urllib.urlopen(endpoint_final_url).read()
                endpoint_final_response = endpoint_response.split(":")[2].split(",")[0].replace('"',"")
                o_system = endpoint_final_response 
            except:
                result.insert(INSERT,"\n"+"ERROR: Unable to get data from esi.evetech.net!")
                result.see("end")
         
            #GET AND DISPLAY THE TOTAL TRIP DISTANCE INCLUDING RETURN TO ORIGIN  
            return_route = create_route(True)        
            return_distance = len(return_route.split(","))        
            result.insert(INSERT,"\n"+"Including fixed end point: "+str(total_distance+return_distance)+"\n")
            result.see("end") 
            
        #RESET VARIABLES SO ANOTHER SET OF WAYPOINTS CAN BE ENTERED   
        previous_routes = []
        total_routes = []
        tested_routes = []
        final_best_route = []        
        routes = []
        optimized_routes = []
        final_routes = []
        waypoints = []
        o_system = ""
        d_system = ""
        origins = []
        destinations = []
        initialized = False
        start_field.delete(0, 'end')
        end_field.delete(0, 'end')
        start_field.insert(0, "Origin")
        end_field.insert(0, "Destination")
        result.insert(INSERT,"\n")
        result.see("end")
    
    #START THE OPTIMIZATION THREAD
    def begin_optimization():
        global waypoint_adding_done
        if waypoint_adding_done == True:
            optimization_thread = threading.Thread(target=optimize)
            optimization_thread.start()   
    
    #CHANGE THE ROUTE PREFERENCE
    def change_preference():
        global prefstr
        if preference.get() == 1: 
            prefstr = "shortest"    
        if preference.get() == 2: 
            prefstr = "secure"    
        if preference.get() == 3: 
            prefstr = "insecure"    
    
    #CHANGE THE FIXED ENDPOINT
    def set_fixed_endpoint():
        global fixed_endpoint_name
        global fixed_endpoint
        if fixed.get() == 1:            
            fixed_endpoint = True 
            fixed_end_field.configure(state=NORMAL)   
        else:          
            fixed_endpoint = False 
            fixed_end_field.configure(state=DISABLED)
     
    #FINALIZE FIXED ENDPOINT       
    def lock_fixed_endpoint(Event=None):
        global fixed_endpoint_name
        fixed_endpoint_name = fixed_end_field.get()
        fixed_end_field.configure(state=DISABLED)
    
    #SETUP BUTTONS   
    fixed = IntVar()
    fixed_end_button = Checkbutton(window, text="Fixed End-Point", variable=fixed,command=set_fixed_endpoint,onvalue = 1, offvalue = 0, bg="gray",font=("Arial Bold", 12))   
    fixed_end_button.pack()     
    preference = IntVar()
    R1 = Radiobutton(window, text="Shortest", variable=preference,value=1,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R1.pack()  
    R2 = Radiobutton(window, text="Secure", variable=preference,value=2,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R2.pack()   
    R3 = Radiobutton(window, text="Insecure", variable=preference,value=3,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R3.pack() 
    button = Button(window, text="Optimize", font=("Arial Bold", 12), bg="gray", fg="blue", command=begin_optimization)
    button.pack()
    end_field.bind("<Return>",add_waypoint) #ALLOWS THE RETURN KEY TO ADD A WAYPOINT INSTEAD OF CLICKING THE BUTTON
    fixed_end_field.bind("<Return>",lock_fixed_endpoint)
    window.mainloop()   
start()

