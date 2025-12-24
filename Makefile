.PHONY: up run down clean clean-full

# Bring up all containers with build (foreground - shows logs)
up:
	docker compose up --build

# Bring up all containers in detached mode with build
run:
	docker compose up -d --build

# Stop all containers
down:
	docker compose down

# Remove all containers and volumes for this project
clean:
	docker compose down -v --remove-orphans

# Full system prune - removes all stopped containers, unused images, and unused volumes
clean-full:
	docker system prune -a -f --volumes
