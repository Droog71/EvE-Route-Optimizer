#IMPORTS
from __future__ import division
import urllib
import Tkinter
from Tkinter import Button, Entry
from Tkconstants import INSERT
import ScrolledText
import threading

#GLOBAL VARIABLES
routes = []
optimized_routes = []
final_routes = []
waypoints = []
o_system = ""
d_system = ""
origins = []
destinations = []
initialized = False

def start():
    #CREATE THE WINDOW
    window = Tkinter.Tk()
    screen_width = window.winfo_screenwidth() # width of the screen
    screen_height = window.winfo_screenheight() # height of the screen
    window.title("EvE Route Optimizer")
    window.geometry('%dx%d+%d+%d' % (450,400,(screen_width/2)-225,(screen_height/2)-200))
    window.configure(background='gray') 
    result = ScrolledText.ScrolledText(window,width=40,height=13)
    result.configure(font=("Arial Bold", 12), fg="white")
    result.configure(background='black') 
    start_field = Entry(window,width=37)
    end_field = Entry(window,width=37)  
    start_field.insert(0, "Origin")
    end_field.insert(0, "Destination")     
    result.pack()
    start_field.pack()
    end_field.pack()
    
    #ADD A WAYPOINT
    def add_waypoint(Event=None): 
        global o_system
        global d_system
        
        o_system = start_field.get()
        d_system = end_field.get()
        if (o_system != "" and d_system != ""):
            try:
                start_field.delete(0, 'end')
                end_field.delete(0, 'end')
                start_field.insert(0, d_system)
                create_route(False)
                result.insert(INSERT,"\n"+"Added Route: "+o_system+" to "+d_system)
                result.see("end")
            except:
                result.insert(INSERT,"\n"+"ERROR: You spelled it wrong!")   
    
    #CREATE ROUTE USING GIVEN WAYPOINTS
    def create_route(optimizing):
        global routes
        global waypoints
        global o_system
        global d_system
        
        #GET ORIGIN ID
        o_base = "https://esi.evetech.net/latest/search/?categories=solar_system&search="
        o_end = "&strict=true"
        o_url = o_base+o_system+o_end
        
        o_response = urllib.urlopen(o_url).read()
        o_split_response = o_response.split(":")
        o_id_section = o_split_response[1]
        o_id_leftbracket = o_id_section.replace('[', '')
        o_id_rightbracket = o_id_leftbracket.replace(']', '')
        o_id_final = o_id_rightbracket.replace('}', '')
        
        #GET DESTINATION ID
        d_base = "https://esi.evetech.net/latest/search/?categories=solar_system&search="
        d_end = "&strict=true"
        d_url = d_base+d_system+d_end
        
        d_response = urllib.urlopen(d_url).read()
        d_split_response = d_response.split(":")
        d_id_section = d_split_response[1]
        d_id_leftbracket = d_id_section.replace('[', '')
        d_id_rightbracket = d_id_leftbracket.replace(']', '')
        d_id_final = d_id_rightbracket.replace('}', '')
        
        #GET ROUTE 
        r_base = "https://esi.evetech.net/latest/route/"
        r_end = "/?datasource=tranquility&flag="
        r_type = "shortest"       
        r_slash = "/"
        r_url = r_base +o_id_final+r_slash+d_id_final+r_end+r_type  
        
        #IF THIS ROUTE IS PART OF THE ORIGINAL REQUEST, ADD IT TO THE LIST
        if optimizing == False:
            r_response = urllib.urlopen(r_url).read()                   
            routes.append(r_response)
            waypoints.append(o_system)
        else:
            r_response = urllib.urlopen(r_url).read()
            return r_response
    
    #OPTIMIZE THE ROUTE
    def optimize():
        global o_system
        global d_system
        global routes
        global waypoints
        global optimized_routes
        global final_routes
        global origins
        global destinations
        global initialized
        
        result.insert(INSERT,"\n")
        last_destination = ""
        last_route = []
        waypoints.append(d_system)
               
        for route in routes:
            split_route = route.split(",")
            origin = split_route[0].split("[")[1]
            begin_url = "https://esi.evetech.net/latest/universe/systems/"
            end_url = "/?datasource=tranquility&language=en-us"
            final_url = begin_url+origin+end_url
            response = urllib.urlopen(final_url).read() 
            final_origin = response.split(":")[2].split(",")[0].replace('"',"")
            
            destination = split_route[len(split_route)-1].split("]")[0]
            d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
            d_end_url = "/?datasource=tranquility&language=en-us"
            d_final_url = d_begin_url+destination+d_end_url
            d_response = urllib.urlopen(d_final_url).read()
            d_final_response = d_response.split(":")[2].split(",")[0].replace('"',"")
            original_destination = d_final_response
            
            o_system = final_origin
            if initialized == False:
                destinations.append(o_system)
                initialized = True
                last_destination = o_system
            elif o_system != last_destination:
                o_system = last_destination
            optimized = False
            for waypoint in waypoints:
                if optimized == False:
                    d_system = waypoint               
                    if o_system != d_system:                                            
                        result.insert(INSERT,"\n"+"Checking route: "+o_system+":"+d_system)
                        result.see("end")
                        potential_route = create_route(True)
                        split_pot = potential_route.split(",")
                        last_route = split_pot
                        if len(split_pot) < len(split_route) and d_system not in destinations and o_system not in origins:
                            optimized_routes.append(potential_route)                    
                            result.insert(INSERT,"\n"+"Optimized: "+o_system+":"+d_system)
                            result.see("end")
                            origins.append(o_system)
                            destinations.append(d_system)
                            last_destination = d_system
                            optimized = True
            if optimized == False and d_system not in destinations and o_system not in origins:
                if final_origin == last_destination:
                    optimized_routes.append(route)
                    result.insert(INSERT,"\n"+"Keeping route...")
                    result.see("end")
                    origins.append(o_system)
                    destinations.append(original_destination)
                    last_destination = original_destination
                else:
                    for waypoint in waypoints:
                        if optimized == False:
                            d_system = waypoint               
                            if o_system != d_system:                                            
                                result.insert(INSERT,"\n"+"Checking route: "+o_system+":"+d_system)
                                result.see("end")
                                potential_route = create_route(True)
                                split_pot = potential_route.split(",")
                                if len(split_pot) < len(last_route) and d_system not in destinations and o_system not in origins:
                                    optimized_routes.append(potential_route)                    
                                    result.insert(INSERT,"\n"+"Optimized route: "+o_system+":"+d_system)
                                    result.see("end")
                                    origins.append(o_system)
                                    destinations.append(d_system)
                                    last_destination = d_system
                                    optimized = True
                                else:
                                    last_route = split_pot
            elif optimized == False:
                for waypoint in waypoints:
                    d_system = waypoint               
                    if o_system != d_system and d_system not in destinations and o_system not in origins:                    
                        result.insert(INSERT,"\n"+"Reconfiguring route: "+o_system+":"+d_system)
                        result.see("end")
                        potential_route = create_route(True)
                        optimized_routes.append(potential_route)                    
                        result.insert(INSERT,"\n"+"Route reconfigured: "+o_system+":"+d_system)
                        result.see("end")
                        origins.append(o_system)
                        destinations.append(d_system)
                        last_destination = d_system
                
        previous_destination = ""
        for route in optimized_routes:
            split_route = route.split(",")
            origin = split_route[0].split("[")[1]
            destination = split_route[len(split_route)-1].split("]")[0]

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
             
            if previous_destination == "":
                previous_destination = o_final_response
                result.insert(INSERT,"\n\n"+"New Route:"+"\n")
                result.see("end")
            
            if o_final_response == previous_destination:
                final_routes.append(route)
                previous_destination = d_final_response                 
                result.insert(INSERT,"\n"+o_final_response+" to "+d_final_response)
                result.see("end")
            else:
                result.insert(INSERT,"\n"+"ERROR: Out of order! "+o_final_response+":"+d_final_response) 
                result.see("end")
                    
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
        optimization_thread = threading.Thread(target=optimize)
        optimization_thread.start()   
        
    button = Button(window, text="Add Waypoint", font=("Arial Bold", 12), bg="gray", fg="blue", command=add_waypoint)
    button.pack()
    button = Button(window, text="Optimize", font=("Arial Bold", 12), bg="gray", fg="blue", command=begin_optimization)
    button.pack()
    window.bind("<Return>",add_waypoint)
    window.mainloop()    
start()

