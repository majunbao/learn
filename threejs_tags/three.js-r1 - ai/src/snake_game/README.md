# Snake Game Project Documentation

## Project Overview
This project is a simple implementation of the classic Snake game using HTML and JavaScript. The game features a snake that moves around the screen, grows when it eats food, and ends when the snake collides with the walls or itself.

## Project Structure
- `game.js`: Contains the game logic, including the snake movement, collision detection, and rendering.
- `index.html`: An entry point HTML file that loads the game.
- `snake_game.html`: Another HTML file that also loads the game.

## Key Components
### game.js
- **Initialization**: Sets up the game variables, including the snake, food, and game state.
- **Game Loop**: Updates the game state and renders the game frame by frame.
- **Collision Detection**: Checks for collisions with the walls, self, and food.
- **Rendering**: Draws the snake and food on the canvas.
- **User Input Handling**: Captures arrow key presses to change the snake's direction.

### index.html and snake_game.html
- Both files contain a canvas element with an ID of `gameCanvas` where the game is rendered.
- They include a script tag that loads the `game.js` file to run the game logic.

## How to Run the Game
1. Open the `index.html` or `snake_game.html` file in a web browser.
2. The game will start automatically, and you can control the snake using the arrow keys.

## Known Issues
- The game may end immediately if the initial positions of the snake and food are not set correctly.
- The canvas size and scaling may need adjustment for better visual clarity.

## Future Improvements
- Add a scoring system to track the length of the snake.
- Implement a start and restart button for the game.
- Improve the visual appearance of the snake and food.
- Add sound effects for eating food and game over.