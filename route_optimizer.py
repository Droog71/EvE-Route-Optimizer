#IMPORTS
from __future__ import division
import urllib
import Tkinter
from Tkinter import Button, Entry, Radiobutton, IntVar
from Tkconstants import INSERT
import ScrolledText
import threading
from __builtin__ import False

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
prefstr = "shortest"

def start():
    #CREATE THE WINDOW 
    global prefstr 
    window = Tkinter.Tk()
    screen_width = window.winfo_screenwidth() # width of the screen
    screen_height = window.winfo_screenheight() # height of the screen
    window.title("EvE Route Optimizer")
    window.geometry('%dx%d+%d+%d' % (800,600,(screen_width/2)-400,(screen_height/2)-300))
    window.configure(background='gray') 
    result = ScrolledText.ScrolledText(window,width=60,height=20)
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
        global prefstr
        
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
        r_type = prefstr   
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
        best_route = []
        sys1 = ""
        sys2 = ""
               
        for route in routes:
            split_route = route.split(",")
            origin = split_route[0].split("[")[1]
            begin_url = "https://esi.evetech.net/latest/universe/systems/"
            end_url = "/?datasource=tranquility&language=en-us"
            final_url = begin_url+origin+end_url
            response = urllib.urlopen(final_url).read() 
            final_origin = response.split(":")[2].split(",")[0].replace('"',"")
            o_system = final_origin
            
            destination = split_route[len(split_route)-1].split("]")[0]
            d_begin_url = "https://esi.evetech.net/latest/universe/systems/"
            d_end_url = "/?datasource=tranquility&language=en-us"
            d_final_url = d_begin_url+destination+d_end_url
            d_response = urllib.urlopen(d_final_url).read()
            d_final_response = d_response.split(":")[2].split(",")[0].replace('"',"")
            original_destination = d_final_response
                        
            if initialized == False:
                destinations.append(o_system)
                initialized = True
                last_destination = o_system
            elif o_system != last_destination:
                o_system = last_destination
            original_optimized = False
            new_optimized = False
            for waypoint in waypoints:
                if o_system != waypoint:
                    d_system = waypoint               
                if o_system == final_origin:                                                                  
                    result.see("end")
                    potential_route = create_route(True)
                    split_pot = potential_route.split(",")
                    last_route = split_pot                        
                    result.insert(INSERT,"\n"+"Checking original route from "+o_system+" for possible optimization.")
                    if len(split_pot) < len(split_route) and d_system not in destinations and o_system not in origins:                
                        best_route = potential_route
                        sys1 = o_system
                        sys2 = d_system
                        original_optimized = True
            if original_optimized == True: #THE ORIGINAL ROUTE WAS OPTIMIZED                                    
                result.insert(INSERT,"\n\n"+"Optimized route vs original: "+sys1+":"+sys2+"\n")
                result.see("end")
                optimized_routes.append(best_route)               
                origins.append(sys1)
                destinations.append(sys2)
                last_destination = sys2
            elif o_system != final_origin: #THE ROUTE HAS BEEN ALTERED
                for waypoint in waypoints:
                        if o_system != waypoint:
                            d_system = waypoint              
                        if o_system != d_system:                                            
                            result.insert(INSERT,"\n"+"Finding the shortest route from "+o_system+" to another waypoint.")
                            result.see("end")
                            potential_route = create_route(True)
                            split_pot = potential_route.split(",")
                            #FIND THE SHORTEST ROUTE FROM THE CURRENT LOCATION TO ANOTHER LOCATION IN THE LIST
                            if len(split_pot) < len(last_route) and d_system not in destinations and o_system not in origins:  
                                best_route = potential_route   
                                sys1 = o_system
                                sys2 = d_system
                                new_optimized = True 
                            else:
                                last_route = split_pot
            #A BETTER ROUTE WAS FOUND
            if new_optimized == True:                                    
                result.insert(INSERT,"\n\n"+"Optimized route vs all possible: "+sys1+":"+sys2+"\n")
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
            #FAILED
            elif original_optimized == False and new_optimized == False:
                finished = False
                for waypoint in waypoints:
                    if finished == False:
                        if o_system != waypoint and waypoint not in destinations:
                            d_system = waypoint               
                            potential_route = create_route(True)                            
                            optimized_routes.append(potential_route)                    
                            result.insert(INSERT,"\n\n"+"No exceptional route found. Creating route: "+o_system+":"+d_system+"\n")
                            result.see("end")
                            origins.append(o_system)
                            destinations.append(d_system)
                            last_destination = d_system
                            finished = True
                
                original_optimized = False
                new_optimized = False  
  
        previous_destination = ""
        for route in optimized_routes:
            split_route = str(route).split(",")
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
        
        #RETURN HOME       
        #split_route = routes[0].split(",")
        #origin = split_route[0].split("[")[1]
        #begin_url = "https://esi.evetech.net/latest/universe/systems/"
        #end_url = "/?datasource=tranquility&language=en-us"
        #final_url = begin_url+origin+end_url
        #response = urllib.urlopen(final_url).read() 
        #final_origin = response.split(":")[2].split(",")[0].replace('"',"")
        #result.insert(INSERT,"\n"+last_destination+" to "+final_origin)
        #result.see("end")
                    
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
    
    def change_preference():
        global prefstr
        if preference.get() == 1: 
            prefstr = "shortest"    
            print prefstr
        if preference.get() == 2: 
            prefstr = "secure"    
            print prefstr
        if preference.get() == 3: 
            prefstr = "insecure"    
            
    preference = IntVar()
    R1 = Radiobutton(window, text="Shortest", variable=preference,value=1,command=change_preference,bg="gray")
    R1.pack()  
    R2 = Radiobutton(window, text="Secure", variable=preference,value=2,command=change_preference,bg="gray")
    R2.pack()   
    R3 = Radiobutton(window, text="Insecure", variable=preference,value=3,command=change_preference,bg="gray")
    R3.pack()      
    button = Button(window, text="Add Waypoint", font=("Arial Bold", 12), bg="gray", fg="blue", command=add_waypoint)
    button.pack()
    button = Button(window, text="Optimize", font=("Arial Bold", 12), bg="gray", fg="blue", command=begin_optimization)
    button.pack()
    window.bind("<Return>",add_waypoint)
    window.mainloop()    
start()

