#IMPORTS
from __future__ import division
import urllib
import Tkinter
from Tkinter import Button, Entry, Radiobutton, IntVar
from Tkconstants import INSERT
import ScrolledText
import threading

#GLOBAL VARIABLES
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
    window.geometry('%dx%d+%d+%d' % (680,620,(screen_width/2)-340,(screen_height/2)-310))
    window.configure(background='gray') 
    result = ScrolledText.ScrolledText(window,width=60,height=20)
    result.configure(font=("Arial Bold", 12), fg="white")
    result.configure(background='black') 
    start_field = Entry(window,width=37,font=("Arial Bold", 12))
    end_field = Entry(window,width=37,font=("Arial Bold", 12)) 
    iteration_field = Entry(window,width=12,font=("Arial Bold", 12)) 
    start_field.insert(0, "Origin")
    end_field.insert(0, "Destination")   
    iteration_field.insert(0, "Cycles")  
    result.pack()
    start_field.pack()
    end_field.pack()
    iteration_field.pack()
    
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

        result.insert(INSERT,"\n")
        last_destination = ""
        last_route = []
        waypoints.append(d_system)
        best_route = []
        sys1 = ""
        sys2 = ""
        
        #GET AND DISPLAY THE TOTAL ROUTE DISTANCE IN NUMBER OF JUMPS
        total_distance = 0
        for route in routes:
            split_route = route.split(",")
            total_distance += len(split_route)            
        result.insert(INSERT,"\n"+"Number of jumps: "+str(total_distance))
        result.see("end")

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
                    
                    #CONVERT ID TO NAME FOR DESTINATION
                    destination = split_route[len(split_route)-1].split("]")[0]
                    d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
                    d_end_url = "/?datasource=tranquility&language=en-us"
                    d_final_url = d_begin_url+destination+d_end_url
                    d_response = urllib.urlopen(d_final_url).read()
                    d_final_response = d_response.split(":")[2].split(",")[0].replace('"',"")
                    original_destination = d_final_response                                
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
                original_optimized = False
                new_optimized = False
                
                #GO THROUGH ALL OF THE WAYPOINTS AND DETERMINE IF THE ORIGINAL ROUTE CAN BE OPTIMIZED
                for waypoint in waypoints:
                    if o_system != waypoint: #PREVENT ROUTING TO THE CURRENT SYSTEM
                        d_system = waypoint              
                    if o_system == final_origin: #THE ORIGINAL ROUTE IS STILL PRESENT                                                                                  
                        potential_route = create_route(True) #CREATE A ROUTE TO GET THE LENGTH IN NUMBER OF JUMPS
                        split_pot = potential_route.split(",")
                        last_route = split_pot                        
                        result.insert(INSERT,"\n"+"Checking original route from "+o_system+" for possible optimization.")
                        result.see("end")
                        if original_optimized == True:
                            split_best = best_route.split(",")
                            if len(split_pot) < len(split_best) and d_system not in destinations and o_system not in origins:                
                                best_route = potential_route
                                sys1 = o_system
                                sys2 = d_system
                        else:
                            if len(split_pot) < len(split_route) and d_system not in destinations and o_system not in origins:                
                                best_route = potential_route
                                sys1 = o_system
                                sys2 = d_system
                                original_optimized = True
                if original_optimized == True: #THE ORIGINAL ROUTE WAS OPTIMIZED                                    
                    result.insert(INSERT,"\n\n"+"Optimized route vs original: "+sys1+" to "+sys2+"\n")
                    result.see("end")
                    optimized_routes.append(best_route)               
                    origins.append(sys1)
                    destinations.append(sys2)
                    last_destination = sys2
                elif o_system != final_origin: #THE ROUTE HAS BEEN ALTERED, SO THE NEXT WAYPOINT IS DETERMINED
                    for waypoint in waypoints:
                        if o_system != waypoint: #PREVENT ROUTING TO THE CURRENT SYSTEM
                            d_system = waypoint                                                         
                            result.insert(INSERT,"\n"+"Finding the shortest route from "+o_system+" to another waypoint.")
                            result.see("end")
                            potential_route = create_route(True) #CREATE A ROUTE TO GET THE LENGTH IN NUMBER OF JUMPS
                            split_pot = potential_route.split(",")
                            #FIND THE SHORTEST ROUTE FROM THE CURRENT LOCATION TO ANOTHER LOCATION IN THE LIST
                            if new_optimized == True:
                                split_best = best_route.split(",")
                                if len(split_pot) < len(split_best) and d_system not in destinations and o_system not in origins:  
                                    best_route = potential_route   
                                    sys1 = o_system
                                    sys2 = d_system  
                            else: 
                                if len(split_pot) < len(last_route) and d_system not in destinations and o_system not in origins:  
                                    best_route = potential_route   
                                    sys1 = o_system
                                    sys2 = d_system
                                    new_optimized = True 
                                else:
                                    last_route = split_pot
                                
                #A BETTER ROUTE WAS FOUND
                if new_optimized == True:                                    
                    result.insert(INSERT,"\n\n"+"Optimized route vs all possible: "+sys1+" to "+sys2+"\n")
                    result.see("end")
                    optimized_routes.append(best_route)                
                    origins.append(sys1)
                    destinations.append(sys2)
                    last_destination = sys2
                    
                #THE ROUTE WAS ALREADY OPTIMAL                            
                elif new_optimized == False and o_system == final_origin and original_optimized == False and d_system not in destinations:
                    optimized_routes.append(route)
                    result.insert(INSERT,"\n\n"+"Keeping original route...\n")
                    result.see("end")
                    origins.append(o_system)
                    destinations.append(original_destination)
                    last_destination = original_destination
                    
                #A BETTER ROUTE WAS NOT FOUND AND THE ORIGINAL IS NOT OPTIMAL, SO THE NEXT WAYPOINT IN THE LIST IS USED
                elif original_optimized == False and new_optimized == False:
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
                                else: #ALL POSSIBLE ROUTES HAVE BEEN EXAMINED FOR THIS WAYPOINT 
                                    previous_route = [None] * 10000
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
                                            if len(route) < len(previous_route):
                                                best_tested_route = route
                                            previous_route = route 
                                    split_route = str(best_tested_route).split(",")                                            
                                    origin = split_route[0].split("[")[1]
                                    destination = split_route[len(split_route)-1].split("]")[0]
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
                                    result.insert(INSERT,"\n\n"+"Best route already found for this waypoint: "+t_o_final_response+" to "+t_d_final_response+"\n")
                                    result.see("end")
                                    origins.append(o_system)
                                    destinations.append(d_system)
                                    last_destination = d_system
                                    finished = True 
                                                        
            total_routes.append(optimized_routes)          
            previous_routes = optimized_routes           
            optimized_routes = []
            origins = []
            destinations = []
            original_optimized = False
            new_optimized = False
            initialized = False
        
        #SELECT THE BEST ROUTE FROM ALL CYCLES
        previous_route = [None] * 10000
        for route in total_routes:
            if len(route) < len(previous_route):
                final_best_route = route
            previous_route = route
                
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
        
        #GET AND DISPLAY THE TOTAL TRIP DISTANCE IN NUMBER OF JUMPS
        total_distance = 0
        for route in final_routes:
            split_route = route.split(",")
            total_distance += len(split_route)
        result.insert(INSERT,"\n\n"+"Number of jumps: "+str(total_distance))
        result.see("end")
        
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
        result.insert(INSERT,"\n"+"Including return to origin: "+str(total_distance+return_distance))
        result.see("end")
                
        #THIS IS HERE TO DISPLAY THE RETURN HOME ROUTE BUT IS NOT NECESSARY     
        #split_route = routes[0].split(",")
        #origin = split_route[0].split("[")[1]
        #begin_url = "https://esi.evetech.net/latest/universe/systems/"
        #end_url = "/?datasource=tranquility&language=en-us"
        #final_url = begin_url+origin+end_url
        #response = urllib.urlopen(final_url).read() 
        #final_origin = response.split(":")[2].split(",")[0].replace('"',"")
        #result.insert(INSERT,"\n"+last_destination+" to "+final_origin)
        #result.see("end")
        
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
    
    #SETUP BUTTONS       
    preference = IntVar()
    R1 = Radiobutton(window, text="Shortest", variable=preference,value=1,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R1.pack()  
    R2 = Radiobutton(window, text="Secure", variable=preference,value=2,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R2.pack()   
    R3 = Radiobutton(window, text="Insecure", variable=preference,value=3,command=change_preference,bg="gray",font=("Arial Bold", 12))
    R3.pack()      
    button = Button(window, text="Add Waypoint", font=("Arial Bold", 12), bg="gray", fg="blue", command=add_waypoint)
    button.pack()
    button = Button(window, text="Optimize", font=("Arial Bold", 12), bg="gray", fg="blue", command=begin_optimization)
    button.pack()
    window.bind("<Return>",add_waypoint) #ALLOWS THE RETURN KEY TO ADD A WAYPOINT INSTEAD OF CLICKING THE BUTTON
    window.mainloop()   
start()

