import bge
import math

def apply_gravity(cont):
    # Get the current object
    obj = cont.owner
    
    # Set gravitational constant
    G = 10.1  # Adjust this value for stronger or weaker gravity
    
    # Get all objects in the scene
    scene = bge.logic.getCurrentScene()
    objects = scene.objects
    
    # Iterate through all objects in the scene
    for other in objects:
        # Check if the other object has the "gravity" property
        if "gravity" in other:
            if other != obj:  # Avoid self-attraction
                # Calculate distance vector
                distance_vector = other.worldPosition - obj.worldPosition
                
                # Calculate distance magnitude
                distance = math.sqrt(distance_vector.x**2 + distance_vector.y**2 + distance_vector.z**2)
                
                # Avoid division by zero
                if distance > 0.1:  # Prevent too close interactions
                    # Calculate gravitational force
                    force_magnitude = G * (obj["gravity"] * other["gravity"]) / (distance * distance)
                    
                    # Normalize the distance vector and scale it by force magnitude
                    force_vector = distance_vector.normalized() * force_magnitude
                    
                    # Apply force to the object's velocity
                    obj.setLinearVelocity(obj.getLinearVelocity() + force_vector, True)

# Main logic execution
if __name__ == "__main__":
    apply_gravity(bge.logic.getCurrentController())
