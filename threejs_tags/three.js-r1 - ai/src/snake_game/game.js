// 游戏配置
const GAME_CONFIG = {
    CANVAS_WIDTH: 600,
    CANVAS_HEIGHT: 400,
    GRID_SIZE: 20,
    INITIAL_SPEED: 150,
    SPEED_INCREMENT: 5,
    MIN_SPEED: 80,
    FOOD_COUNT: 1,
    POWER_UP_CHANCE: 0.1,
    DIFFICULTY_LEVELS: {
        easy: { speed: 200, foodCount: 1 },
        medium: { speed: 150, foodCount: 1 },
        hard: { speed: 100, foodCount: 2 },
        expert: { speed: 80, foodCount: 3 }
    }
};

// 当前游戏难度
let currentDifficulty = 'medium';

// 游戏模式
const GAME_MODES = {
    NORMAL: 'normal',
    SPEED: 'speed',
    INVINCIBLE: 'invincible'
};

let currentMode = GAME_MODES.NORMAL;

// 音效管理
const SoundManager = {
    sounds: {},
    
    init() {
        // 创建简单的音效（使用Web Audio API）
        this.createSound('eat', 523.25, 0.1); // C5 note
        this.createSound('powerUp', 659.25, 0.1); // E5 note
        this.createSound('gameOver', 261.63, 0.2); // C4 note
        this.createSound('speedBoost', 783.99, 0.1); // G5 note
    },
    
    createSound(name, frequency, duration) {
        // 创建简单的声音效果
        this.sounds[name] = { frequency, duration };
    },
    
    play(name) {
        // 在实际应用中，这里会播放声音
        // 为了简化，我们只做日志输出
        console.log(`Playing sound: ${name}`);
    }
};

// 游戏状态
let gameState = {
    snake: [],
    food: [],
    powerUps: [],
    direction: 'right',
    nextDirection: 'right',
    score: 0,
    highScore: parseInt(localStorage.getItem('snakeHighScore') || '0'),
    length: 1,
    speed: GAME_CONFIG.INITIAL_SPEED,
    isRunning: false,
    isPaused: false,
    gameLoop: null
};

// DOM 元素
const elements = {
    canvas: document.getElementById('game-canvas'),
    ctx: null,
    score: document.getElementById('score'),
    highScore: document.getElementById('high-score'),
    length: document.getElementById('length'),
    speed: document.getElementById('speed'),
    foodCount: document.getElementById('food-count'),
    startScreen: document.getElementById('start-screen'),
    gameOverScreen: document.getElementById('game-over-screen'),
    finalScore: document.getElementById('final-score'),
    finalHighScore: document.getElementById('final-high-score'),
    startBtn: document.getElementById('start-btn'),
    pauseBtn: document.getElementById('pause-btn'),
    resetBtn: document.getElementById('reset-btn'),
    restartBtn: document.getElementById('restart-btn'),
    beginGameBtn: document.getElementById('begin-game-btn')
};

// 初始化游戏
function initGame() {
    elements.ctx = elements.canvas.getContext('2d');
    SoundManager.init();
    setupEventListeners();
    updateUI();
    renderStartScreen();
}

// 设置事件监听器
function setupEventListeners() {
    // 键盘控制
    document.addEventListener('keydown', handleKeyPress);
    
    // 按钮控制
    elements.startBtn.addEventListener('click', startGame);
    elements.pauseBtn.addEventListener('click', togglePause);
    elements.resetBtn.addEventListener('click', resetGame);
    elements.restartBtn.addEventListener('click', resetGame);
    elements.beginGameBtn.addEventListener('click', startGame);
    
    // 触摸控制（移动端）
    let touchStartX = 0;
    let touchStartY = 0;
    
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        
        const dx = touchEndX - touchStartX;
        const dy = touchEndY - touchStartY;
        
        if (Math.abs(dx) > Math.abs(dy)) {
            // 水平滑动
            if (dx > 0 && gameState.direction !== 'left') {
                gameState.nextDirection = 'right';
            } else if (dx < 0 && gameState.direction !== 'right') {
                gameState.nextDirection = 'left';
            }
        } else {
            // 垂直滑动
            if (dy > 0 && gameState.direction !== 'up') {
                gameState.nextDirection = 'down';
            } else if (dy < 0 && gameState.direction !== 'down') {
                gameState.nextDirection = 'up';
            }
        }
    });
}

// 处理键盘输入
function handleKeyPress(e) {
    switch (e.key) {
        case 'ArrowUp':
            if (gameState.direction !== 'down') {
                gameState.nextDirection = 'up';
            }
            break;
        case 'ArrowDown':
            if (gameState.direction !== 'up') {
                gameState.nextDirection = 'down';
            }
            break;
        case 'ArrowLeft':
            if (gameState.direction !== 'right') {
                gameState.nextDirection = 'left';
            }
            break;
        case 'ArrowRight':
            if (gameState.direction !== 'left') {
                gameState.nextDirection = 'right';
            }
            break;
        case ' ':
            if (gameState.isRunning) {
                togglePause();
            }
            break;
        case 'r':
        case 'R':
            if (!gameState.isRunning) {
                resetGame();
            }
            break;
    }
}

// 开始游戏
function startGame() {
    if (gameState.isRunning) return;
    
    resetGameState();
    gameState.isRunning = true;
    gameState.isPaused = false;
    elements.startScreen.classList.add('hidden');
    elements.gameOverScreen.classList.add('hidden');
    
    // 启动游戏循环
    if (gameState.gameLoop) {
        clearInterval(gameState.gameLoop);
    }
    
    gameState.gameLoop = setInterval(update, gameState.speed);
    updateUI();
}

// 切换暂停状态
function togglePause() {
    if (!gameState.isRunning) return;
    
    gameState.isPaused = !gameState.isPaused;
    elements.pauseBtn.textContent = gameState.isPaused ? '继续' : '暂停';
    updateUI();
}

// 重置游戏
function resetGame() {
    clearInterval(gameState.gameLoop);
    gameState.isRunning = false;
    gameState.isPaused = false;
    elements.startScreen.classList.remove('hidden');
    elements.gameOverScreen.classList.add('hidden');
    updateUI();
}

// 重置游戏状态
function resetGameState() {
    // 初始化蛇
    gameState.snake = [
        {x: 10, y: 10},
        {x: 9, y: 10},
        {x: 8, y: 10}
    ];
    
    // 重置游戏变量
    gameState.direction = 'right';
    gameState.nextDirection = 'right';
    gameState.score = 0;
    gameState.length = 3;
    gameState.speed = GAME_CONFIG.INITIAL_SPEED;
    
    // 生成食物
    generateFood();
    generatePowerUps();
    
    updateUI();
}

// 生成食物
function generateFood() {
    gameState.food = [];
    for (let i = 0; i < GAME_CONFIG.FOOD_COUNT; i++) {
        let newFood;
        let validPosition = false;
        
        while (!validPosition) {
            newFood = {
                x: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_WIDTH / GAME_CONFIG.GRID_SIZE)),
                y: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_HEIGHT / GAME_CONFIG.GRID_SIZE))
            };
            
            // 检查是否与蛇身重叠
            validPosition = !gameState.snake.some(segment => 
                segment.x === newFood.x && segment.y === newFood.y
            );
            
            // 检查是否与现有食物重叠
            if (gameState.food.some(f => f.x === newFood.x && f.y === newFood.y)) {
                validPosition = false;
            }
        }
        
        gameState.food.push(newFood);
    }
    
    updateUI();
}

// 生成道具
function generatePowerUps() {
    gameState.powerUps = [];
    
    // 有概率生成特殊道具
    if (Math.random() < GAME_CONFIG.POWER_UP_CHANCE) {
        let newPowerUp;
        let validPosition = false;
        
        while (!validPosition) {
            newPowerUp = {
                x: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_WIDTH / GAME_CONFIG.GRID_SIZE)),
                y: Math.floor(Math.random() * (GAME_CONFIG.CANVAS_HEIGHT / GAME_CONFIG.GRID_SIZE)),
                type: Math.random() < 0.5 ? 'speed' : 'score'
            };
            
            // 检查是否与蛇身或食物重叠
            validPosition = !gameState.snake.some(segment => 
                segment.x === newPowerUp.x && segment.y === newPowerUp.y
            ) && !gameState.food.some(f => 
                f.x === newPowerUp.x && f.y === newPowerUp.y
            );
        }
        
        gameState.powerUps.push(newPowerUp);
    }
}

// 更新游戏状态
function update() {
    if (gameState.isPaused || !gameState.isRunning) return;
    
    // 更新方向
    gameState.direction = gameState.nextDirection;
    
    // 计算新的头部位置
    const head = {...gameState.snake[0]};
    
    switch (gameState.direction) {
        case 'up':
            head.y -= 1;
            break;
        case 'down':
            head.y += 1;
            break;
        case 'left':
            head.x -= 1;
            break;
        case 'right':
            head.x += 1;
            break;
    }
    
    // 检查碰撞边界
    if (head.x < 0 || head.x >= GAME_CONFIG.CANVAS_WIDTH / GAME_CONFIG.GRID_SIZE ||
        head.y < 0 || head.y >= GAME_CONFIG.CANVAS_HEIGHT / GAME_CONFIG.GRID_SIZE) {
        gameOver();
        return;
    }
    
    // 检查碰撞自身
    if (gameState.snake.some(segment => segment.x === head.x && segment.y === head.y)) {
        gameOver();
        return;
    }
    
    // 添加新头部
    gameState.snake.unshift(head);
    
    // 检查是否吃到食物
    let ateFood = false;
    let atePowerUp = false;
    
    // 检查食物
    for (let i = 0; i < gameState.food.length; i++) {
        if (head.x === gameState.food[i].x && head.y === gameState.food[i].y) {
            ateFood = true;
            gameState.food.splice(i, 1);
            break;
        }
    }
    
    // 检查道具
    for (let i = 0; i < gameState.powerUps.length; i++) {
        if (head.x === gameState.powerUps[i].x && head.y === gameState.powerUps[i].y) {
            atePowerUp = true;
            applyPowerUp(gameState.powerUps[i].type);
            gameState.powerUps.splice(i, 1);
            break;
        }
    }
    
    // 如果没有吃到食物，则移除尾部
    if (!ateFood && !atePowerUp) {
        gameState.snake.pop();
    } else {
        // 如果吃到食物，增加长度和分数
        if (ateFood) {
            gameState.score += 10;
            gameState.length++;
        }
        
        // 生成新食物
        generateFood();
        
        // 生成新道具
        generatePowerUps();
        
        // 提高速度
        if (gameState.speed > GAME_CONFIG.MIN_SPEED) {
            gameState.speed = Math.max(GAME_CONFIG.MIN_SPEED, gameState.speed - GAME_CONFIG.SPEED_INCREMENT);
            if (gameState.gameLoop) {
                clearInterval(gameState.gameLoop);
                gameState.gameLoop = setInterval(update, gameState.speed);
            }
        }
    }
    
    updateUI();
}

// 应用道具效果
function applyPowerUp(type) {
    switch (type) {
        case 'speed':
            // 加速效果
            if (gameState.speed > GAME_CONFIG.MIN_SPEED + 30) {
                gameState.speed -= 30;
                if (gameState.gameLoop) {
                    clearInterval(gameState.gameLoop);
                    gameState.gameLoop = setInterval(update, gameState.speed);
                }
            }
            SoundManager.play('speedBoost');
            break;
        case 'score':
            // 得分加成
            gameState.score += 50;
            SoundManager.play('powerUp');
            break;
    }
}

// 游戏结束
function gameOver() {
    clearInterval(gameState.gameLoop);
    gameState.isRunning = false;
    
    // 更新最高分
    if (gameState.score > gameState.highScore) {
        gameState.highScore = gameState.score;
        localStorage.setItem('snakeHighScore', gameState.highScore.toString());
    }
    
    // 添加游戏结束动画效果
    animateGameOver();
    
    // 显示游戏结束屏幕
    elements.finalScore.textContent = gameState.score;
    elements.finalHighScore.textContent = gameState.highScore;
    elements.gameOverScreen.classList.remove('hidden');
    updateUI();
}

// 游戏结束动画效果
function animateGameOver() {
    const canvas = elements.canvas;
    const ctx = elements.ctx;
    const gridSize = GAME_CONFIG.GRID_SIZE;
    
    // 创建爆炸效果
    const explosionParticles = [];
    for (let i = 0; i < 50; i++) {
        explosionParticles.push({
            x: Math.random() * GAME_CONFIG.CANVAS_WIDTH,
            y: Math.random() * GAME_CONFIG.CANVAS_HEIGHT,
            size: Math.random() * 5 + 2,
            speedX: (Math.random() - 0.5) * 5,
            speedY: (Math.random() - 0.5) * 5,
            color: `hsl(${Math.random() * 360}, 100%, 50%)`
        });
    }
    
    // 动画函数
    let animationFrame = 0;
    const animate = () => {
        animationFrame++;
        
        // 清除画布
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(0, 0, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.CANVAS_HEIGHT);
        
        // 绘制粒子效果
        explosionParticles.forEach(particle => {
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            particle.size *= 0.95;
            
            ctx.fillStyle = particle.color;
            ctx.globalAlpha = particle.size / 10;
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
        });
        
        ctx.globalAlpha = 1;
        
        // 继续动画直到结束
        if (animationFrame < 30) {
            requestAnimationFrame(animate);
        }
    };
    
    animate();
}

// 更新UI
function updateUI() {
    elements.score.textContent = gameState.score;
    elements.highScore.textContent = gameState.highScore;
    elements.length.textContent = gameState.length;
    elements.speed.textContent = Math.round((GAME_CONFIG.INITIAL_SPEED - gameState.speed + GAME_CONFIG.MIN_SPEED) / 10);
    elements.foodCount.textContent = gameState.food.length;
    
    // 更新按钮状态
    elements.pauseBtn.textContent = gameState.isPaused ? '继续' : '暂停';
    elements.pauseBtn.disabled = !gameState.isRunning || gameState.isPaused;
    
    // 渲染游戏画面
    render();
}

// 渲染游戏画面
function render() {
    const ctx = elements.ctx;
    const gridSize = GAME_CONFIG.GRID_SIZE;
    
    // 清空画布
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(0, 0, GAME_CONFIG.CANVAS_WIDTH, GAME_CONFIG.CANVAS_HEIGHT);
    
    // 绘制网格背景
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 0.5;
    
    for (let x = 0; x <= GAME_CONFIG.CANVAS_WIDTH; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, GAME_CONFIG.CANVAS_HEIGHT);
        ctx.stroke();
    }
    
    for (let y = 0; y <= GAME_CONFIG.CANVAS_HEIGHT; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(GAME_CONFIG.CANVAS_WIDTH, y);
        ctx.stroke();
    }
    
    // 绘制蛇
    gameState.snake.forEach((segment, index) => {
        if (index === 0) {
            // 蛇头
            ctx.fillStyle = '#4CAF50';
            ctx.shadowColor = 'rgba(76, 175, 80, 0.7)';
        } else {
            // 蛇身
            const colorValue = 150 - Math.min(100, index * 2);
            ctx.fillStyle = `rgb(76, ${colorValue}, 76)`;
            ctx.shadowColor = 'rgba(76, 175, 80, 0.3)';
        }
        
        // 添加渐变效果
        const gradient = ctx.createRadialGradient(
            segment.x * gridSize + gridSize / 2,
            segment.y * gridSize + gridSize / 2,
            0,
            segment.x * gridSize + gridSize / 2,
            segment.y * gridSize + gridSize / 2,
            gridSize / 2
        );
        
        if (index === 0) {
            gradient.addColorStop(0, '#8BC34A');
            gradient.addColorStop(1, '#4CAF50');
        } else {
            const colorValue = 150 - Math.min(100, index * 2);
            gradient.addColorStop(0, `rgb(100, ${colorValue + 20}, 100)`);
            gradient.addColorStop(1, `rgb(76, ${colorValue}, 76)`);
        }
        
        ctx.shadowBlur = 10;
        ctx.fillStyle = gradient;
        ctx.fillRect(segment.x * gridSize, segment.y * gridSize, gridSize, gridSize);
        ctx.shadowBlur = 0;
        
        // 添加边框
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.lineWidth = 1;
        ctx.strokeRect(segment.x * gridSize, segment.y * gridSize, gridSize, gridSize);
    });
    
    // 绘制食物
    gameState.food.forEach(food => {
        ctx.fillStyle = '#FF5252';
        ctx.shadowColor = 'rgba(255, 82, 82, 0.7)';
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(
            food.x * gridSize + gridSize / 2,
            food.y * gridSize + gridSize / 2,
            gridSize / 2,
            0,
            Math.PI * 2
        );
        ctx.fill();
        ctx.shadowBlur = 0;
        
        // 添加脉冲效果
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(
            food.x * gridSize + gridSize / 2,
            food.y * gridSize + gridSize / 2,
            gridSize / 2 + 2,
            0,
            Math.PI * 2
        );
        ctx.stroke();
    });
    
    // 绘制道具
    gameState.powerUps.forEach(powerUp => {
        ctx.fillStyle = powerUp.type === 'speed' ? '#2196F3' : '#FFC107';
        ctx.shadowColor = powerUp.type === 'speed' ? 'rgba(33, 150, 243, 0.7)' : 'rgba(255, 193, 7, 0.7)';
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(
            powerUp.x * gridSize + gridSize / 2,
            powerUp.y * gridSize + gridSize / 2,
            gridSize / 2,
            0,
            Math.PI * 2
        );
        ctx.fill();
        ctx.shadowBlur = 0;
        
        // 添加闪烁效果
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(
            powerUp.x * gridSize + gridSize / 2,
            powerUp.y * gridSize + gridSize / 2,
            gridSize / 2 + 1,
            0,
            Math.PI * 2
        );
        ctx.stroke();
        
        // 添加图标
        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(
            powerUp.type === 'speed' ? '⚡' : '⭐',
            powerUp.x * gridSize + gridSize / 2,
            powerUp.y * gridSize + gridSize / 2
        );
    });
}

// 渲染开始屏幕
function renderStartScreen() {
    elements.startScreen.classList.remove('hidden');
    elements.gameOverScreen.classList.add('hidden');
}

// 初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    initGame();
});

// 导出函数供外部使用（如果需要）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        startGame,
        togglePause,
        resetGame,
        updateUI
    };
}