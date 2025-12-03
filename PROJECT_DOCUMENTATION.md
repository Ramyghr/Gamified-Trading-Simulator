# Project Documentation

## Models

### `app/models/base.py`

This file defines the base class for all SQLAlchemy models in the application.

-   **`Base`**: An instance of `declarative_base()` from SQLAlchemy. All database models inherit from this class. This allows SQLAlchemy's ORM to map the Python classes to database tables.

### `app/models/bot.py`

This file defines the SQLAlchemy models related to trading bots, their configurations, individual trades, backtesting results, and execution logs.

#### Enums:

*   **`BotStatus`**: Defines the possible operational states of a trading bot (`ACTIVE`, `PAUSED`, `STOPPED`, `ERROR`).
*   **`BotStrategyType`**: Enumerates various supported trading strategies for bots, such as `MA_CROSSOVER`, `RSI_OVERSOLD_OVERBOUGHT`, `BOLLINGER_BANDS`, `MACD_CROSSOVER`, `VOLUME_BREAKOUT`, `MEAN_REVERSION`, `MOMENTUM`, `SUPPORT_RESISTANCE`, `GRID_TRADING`, `DCA`, and `RAPID_TEST`.
*   **`TradeAction`**: Specifies the actions a bot can take (`BUY`, `SELL`, `HOLD`).

#### Models:

*   **`Bot`**: Represents the configuration and state of a trading bot.
    *   **Purpose**: Allows users to create and manage automated trading strategies.
    *   **Fields**:
        *   `id`: Unique identifier for the bot.
        *   `user_id`: Foreign key to the `User` model, indicating ownership.
        *   `portfolio_id`: Foreign key to the `Portfolio` model, linking the bot to a specific portfolio.
        *   `name`, `description`: Basic information about the bot.
        *   `strategy_type`: The trading strategy employed by the bot (from `BotStrategyType` enum).
        *   `strategy_params`: JSON field for strategy-specific configuration parameters.
        *   `symbol`, `asset_type`: The trading instrument (e.g., stock symbol) and its type.
        *   `max_position_size`, `stop_loss_pct`, `take_profit_pct`, `max_daily_trades`, `max_daily_loss`, `max_open_trades`: Risk management parameters.
        *   `use_leverage`, `leverage`: Optional leverage settings.
        *   `interval`: Execution frequency (e.g., "5m", "1h").
        *   `status`: Current operational status (from `BotStatus` enum).
        *   `is_backtesting`: Boolean flag indicating if the bot is in backtesting mode.
        *   `total_trades`, `winning_trades`, `losing_trades`, `total_pnl`, `total_fees`: Performance tracking metrics.
        *   `last_execution`, `next_execution`, `last_signal`: Execution tracking timestamps and signals.
        *   `created_at`, `updated_at`, `activated_at`, `stopped_at`: Timestamps for lifecycle events.
    *   **Relationships**:
        *   `user`: Many-to-one relationship with `User`.
        *   `portfolio`: Many-to-one relationship with `Portfolio`.
        *   `trades`: One-to-many relationship with `BotTrade` (individual trades made by the bot).
        *   `backtests`: One-to-many relationship with `BotBacktest` (backtesting results).
        *   `logs`: One-to-many relationship with `BotLog` (execution logs).

*   **`BotTrade`**: Records individual trades executed by a trading bot.
    *   **Purpose**: Provides a granular history of a bot's trading activity.
    *   **Fields**:
        *   `id`: Unique identifier for the trade.
        *   `bot_id`: Foreign key to the `Bot` model.
        *   `user_id`: Foreign key to the `User` model.
        *   `symbol`: The traded instrument.
        *   `action`: Whether the trade was a `BUY` or `SELL`.
        *   `quantity`, `entry_price`, `exit_price`: Trade details.
        *   `trade_value`, `fee`, `pnl`, `pnl_pct`: Financial outcomes of the trade.
        *   `leverage_used`, `margin_used`: Leverage-related information.
        *   `stop_loss_price`, `take_profit_price`, `exit_reason`: Risk management and exit details.
        *   `is_open`: Boolean indicating if the trade is still active.
        *   `opened_at`, `closed_at`: Timestamps for trade initiation and closure.
    *   **Relationships**:
        *   `bot`: Many-to-one relationship with `Bot`.
        *   `user`: Many-to-one relationship with `User`.

*   **`BotBacktest`**: Stores the results of a bot's backtesting process.
    *   **Purpose**: Allows users to evaluate bot performance on historical data without live market exposure.
    *   **Fields**:
        *   `id`: Unique identifier for the backtest.
        *   `bot_id`: Foreign key to the `Bot` model.
        *   `user_id`: Foreign key to the `User` model.
        *   `start_date`, `end_date`, `initial_capital`: Backtest configuration parameters.
        *   `final_capital`, `total_return`, `total_return_pct`: Overall performance metrics.
        *   `total_trades`, `winning_trades`, `losing_trades`, `win_rate`: Trade statistics.
        *   `avg_win`, `avg_loss`, `largest_win`, `largest_loss`: Detailed trade performance.
        *   `profit_factor`, `sharpe_ratio`, `max_drawdown`, `max_drawdown_pct`: Risk-adjusted performance metrics.
        *   `performance_metrics`: JSON field for detailed day-by-day performance data.
        *   `trade_history`: JSON field for a list of all trades made during the backtest.
        *   `status`, `error_message`: Backtest execution status and any errors.
        *   `started_at`, `completed_at`: Timestamps for backtest execution.
    *   **Relationships**:
        *   `bot`: Many-to-one relationship with `Bot`.
        *   `user`: Many-to-one relationship with `User`.

*   **`BotLog`**: Stores logs generated during a bot's execution (both live and backtesting).
    *   **Purpose**: Facilitates debugging, monitoring, and auditing of bot operations.
    *   **Fields**:
        *   `id`: Unique identifier for the log entry.
        *   `bot_id`: Foreign key to the `Bot` model.
        *   `level`: Severity of the log entry (e.g., `INFO`, `WARNING`, `ERROR`).
        *   `message`: The log message.
        *   `details`: JSON field for additional structured log details.
        *   `timestamp`: When the log entry was created.
    *   **Relationships**:
        *   `bot`: Many-to-one relationship with `Bot`.

### `app/models/candle.py`

This file defines the SQLAlchemy model for storing candlestick data, which is crucial for financial market analysis and charting.

#### Models:

*   **`Candle`**: Represents a single candlestick data point for a specific financial instrument and timeframe.
    *   **Purpose**: Stores Open, High, Low, Close, and Volume (OHLCV) data along with other metrics for a given symbol and timeframe.
    *   **Fields**:
        *   `id`: Unique identifier for the candle.
        *   `symbol`: The ticker symbol of the financial instrument (e.g., "AAPL", "BTC/USD").
        *   `timeframe`: The time interval represented by the candle (e.g., "1m", "5m", "1h", "1d"), using the `Timeframe` enum from `app.constants.timeframes`.
        *   `open`: The opening price of the period.
        *   `high`: The highest price of the period.
        *   `low`: The lowest price of the period.
        *   `close`: The closing price of the period.
        *   `volume`: The trading volume during the period.
        *   `vwap`: Volume Weighted Average Price (optional).
        *   `trades`: Number of trades within the period (optional).
        *   `timestamp`: The timestamp marking the beginning or end of the candle's period.
        *   `created_at`: The timestamp when the record was created in the database.
    *   **Indexes**:
        *   `idx_symbol_timeframe_timestamp`: Ensures fast lookups by symbol, timeframe, and timestamp.

### `app/models/crisis_simulator.py`

This file defines the SQLAlchemy models for managing market crisis simulations, participants, their trading activities within simulations, leaderboard, and historical snapshots. This is a core gamified feature of the application, allowing users to experience historical market events.

#### Enums:

*   **`CrisisType`**: Enumerates the types of historical market crises that can be simulated (e.g., `GREAT_DEPRESSION`, `BLACK_MONDAY`, `DOTCOM_BUBBLE`, `FINANCIAL_CRISIS_2008`, `COVID_CRASH`).
*   **`SimulationStatus`**: Defines the current state of a simulation (`PENDING`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`).

#### Models:

*   **`CrisisSimulation`**: Represents a single market crisis simulation event.
    *   **Purpose**: Configures and tracks the overall state of a simulation.
    *   **Fields**:
        *   `id`: Unique identifier for the simulation.
        *   `crisis_type`: The type of historical crisis being simulated (from `CrisisType` enum).
        *   `status`: The current status of the simulation (from `SimulationStatus` enum).
        *   `real_start_time`, `real_end_time`: Actual start and end times of the simulation.
        *   `historical_start_date`, `historical_end_date`: The historical period covered by the simulation.
        *   `current_historical_time`: The current point in the historical timeline being simulated.
        *   `duration_minutes`: The real-world duration of the simulation (e.g., 60 minutes).
        *   `time_compression_ratio`: How much historical time is compressed into real time.
        *   `phase_config`, `current_phase`: Configuration and tracking of different phases within the simulation.
        *   `created_by`: The ID of the administrator who created the simulation.
        *   `created_at`, `started_at`, `completed_at`: Timestamps for creation, start, and completion.
        *   `max_participants`: Maximum number of users who can join the simulation.
        *   `is_competitive`: Flag indicating if the simulation has a competitive leaderboard.
    *   **Relationships**:
        *   `participants`: One-to-many relationship with `SimulationParticipant`.
        *   `leaderboard`: One-to-many relationship with `SimulationLeaderboard`.

*   **`SimulationParticipant`**: Represents a user's participation in a specific crisis simulation.
    *   **Purpose**: Tracks an individual user's state, performance, and behavior within a simulation.
    *   **Fields**:
        *   `id`: Unique identifier for the participant entry.
        *   `simulation_id`: Foreign key to the `CrisisSimulation` model.
        *   `user_id`: The ID of the participating user.
        *   `joined_at`, `finished_at`: Timestamps for joining and finishing.
        *   `is_active`: Boolean indicating if the participant is currently active.
        *   `initial_cash`, `initial_portfolio_value`: Starting capital for the simulation.
        *   `current_cash`, `current_portfolio_value`, `current_total_value`: Real-time portfolio metrics within the simulation.
        *   `total_return_pct`, `max_drawdown_pct`, `sharpe_ratio`: Performance metrics.
        *   `total_trades`, `profitable_trades`: Trade statistics.
        *   `max_leverage_used`, `margin_calls_count`: Risk metrics.
        *   `detected_biases`: JSON field to store identified behavioral biases.
        *   `final_rank`, `final_score`: Final ranking and score if competitive.
    *   **Relationships**:
        *   `simulation`: Many-to-one relationship with `CrisisSimulation`.
        *   `orders`: One-to-many relationship with `SimulationOrder`.
        *   `positions`: One-to-many relationship with `SimulationPosition`.

*   **`SimulationOrder`**: Represents an order placed by a participant within a crisis simulation.
    *   **Purpose**: Isolates simulation-specific orders from live trading orders, allowing independent tracking.
    *   **Fields**:
        *   `id`: Unique identifier for the simulation order.
        *   `participant_id`: Foreign key to the `SimulationParticipant` model.
        *   `symbol`: The instrument being traded.
        *   `order_type`, `side`, `quantity`: Details of the order.
        *   `limit_price`, `stop_price`, `filled_price`, `filled_quantity`: Pricing and fill details.
        *   `status`: Current status of the simulation order.
        *   `placed_at_historical`, `filled_at_historical`: Timestamps in historical simulation time.
        *   `placed_at_real`, `filled_at_real`: Timestamps in real-world time.
        *   `commission`, `rejection_reason`: Execution details.
    *   **Relationships**:
        *   `participant`: Many-to-one relationship with `SimulationParticipant`.

*   **`SimulationPosition`**: Represents an open position held by a participant during a crisis simulation.
    *   **Purpose**: Tracks an individual's holdings within the simulated market.
    *   **Fields**:
        *   `id`: Unique identifier for the simulation position.
        *   `participant_id`: Foreign key to the `SimulationParticipant` model.
        *   `symbol`: The instrument of the position.
        *   `quantity`, `average_cost`, `current_price`: Position details.
        *   `unrealized_pnl`, `unrealized_pnl_pct`, `realized_pnl`: Profit and Loss metrics.
        *   `opened_at`, `last_updated`: Timestamps.
    *   **Relationships**:
        *   `participant`: Many-to-one relationship with `SimulationParticipant`.

*   **`SimulationLeaderboard`**: Stores real-time ranking data for competitive simulations.
    *   **Purpose**: Provides dynamic leaderboard updates during active simulations.
    *   **Fields**:
        *   `id`: Unique identifier.
        *   `simulation_id`: Foreign key to `CrisisSimulation`.
        *   `user_id`: The ID of the user on the leaderboard.
        *   `current_rank`, `previous_rank`: Ranking information.
        *   `total_value`, `total_return_pct`, `sharpe_ratio`: Performance metrics for ranking.
        *   `competition_score`: A weighted score for competitive ranking.
        *   `snapshot_at_historical`, `updated_at`: Timestamps.
    *   **Relationships**:
        *   `simulation`: Many-to-one relationship with `CrisisSimulation`.

*   **`SimulationSnapshot`**: Captures periodic states of participant portfolios during a simulation.
    *   **Purpose**: Enables time-travel, replay, or detailed analysis of simulation events.
    *   **Fields**:
        *   `id`: Unique identifier.
        *   `participant_id`: Foreign key to `SimulationParticipant`.
        *   `historical_time`: The historical timestamp of the snapshot.
        *   `real_time`: The real-world timestamp when the snapshot was taken.
        *   `portfolio_state`: JSON field containing the full portfolio state (cash, positions, total value) at that moment.
        *   `total_return_pct`, `total_value`: Performance metrics at the snapshot time.

### `app/models/lesson.py`

This file defines the SQLAlchemy models for the application's gamified learning system, including lessons and quiz questions.

#### Models:

*   **`Lesson`**: Represents a single educational lesson within the platform.
    *   **Purpose**: To structure learning content (videos, quizzes, simulations, scenarios) and track user progress.
    *   **Fields**:
        *   `id`: Unique identifier for the lesson.
        *   `title`, `description`: Title and descriptive text for the lesson.
        *   `chapter`, `order`: Used for organizing lessons into chapters and defining their sequence.
        *   `type`: Specifies the format of the lesson (e.g., "video", "quiz", "simulation", "scenario").
        *   `difficulty`: Indicates the target skill level ("beginner", "intermediate", "advanced").
        *   `content`: A JSON field that holds the main content, varying by `type` (e.g., video URL, quiz questions, scenario data).
        *   `duration_minutes`: Estimated time to complete the lesson.
        *   `xp_reward`, `coin_reward`, `badge_reward`: Rewards users receive upon completion.
        *   `prerequisite_lesson_id`: Foreign key to another `Lesson` model, indicating a dependency.
        *   `required_level`: The user level needed to access the lesson.
        *   `is_active`, `is_published`: Status flags for lesson availability.
        *   `tags`: JSON field for categorization (e.g., ["stocks", "risk-management"]).
        *   `thumbnail_url`: URL to an image representing the lesson.
        *   `created_at`, `updated_at`: Timestamps for record management.
    *   **Relationships**:
        *   `prerequisite`: Self-referencing relationship to another `Lesson` model.
        *   `user_progress`: One-to-many relationship with `UserLessonProgress`.
        *   `quiz_questions`: One-to-many relationship with `LessonQuizQuestion`.

*   **`LessonQuizQuestion`**: Represents a question within a quiz-type lesson.
    *   **Purpose**: To define the questions, options, and correct answers for interactive quizzes.
    *   **Fields**:
        *   `id`: Unique identifier for the question.
        *   `lesson_id`: Foreign key to the `Lesson` model this question belongs to.
        *   `question_text`: The actual text of the question.
        *   `question_type`: Type of question (e.g., "multiple_choice", "true_false").
        *   `options`: JSON field for possible answers (e.g., `{"A": "Option 1", "B": "Option 2"}`).
        *   `correct_answer`: The correct option for the question (e.g., "A", "true").
        *   `explanation`: Optional explanatory text shown after the user answers.
        *   `points`: Points awarded for a correct answer.
        *   `order`: The display order of the question within the quiz.
        *   `created_at`: Timestamp for record creation.
    *   **Relationships**:
        *   `lesson`: Many-to-one relationship with `Lesson`.
### `app/models/market_subscription.py`

This file defines the SQLAlchemy model for tracking client subscriptions to real-time market data streams.

#### Models:

*   **`MarketSubscription`**: Represents a subscription of a single client to a specific market data symbol.
    *   **Purpose**: To manage which clients are subscribed to which real-time data streams, likely over WebSockets.
    *   **Fields**:
        *   `id`: Unique identifier for the subscription.
        *   `connection_id`: A unique identifier for the client's connection (e.g., a WebSocket connection ID).
        *   `symbol`: The ticker symbol of the financial instrument the client is subscribed to.
        *   `is_active`: A boolean flag indicating if the subscription is currently active.
        *   `created_at`: The timestamp when the subscription was created.
        *   `last_heartbeat`: A timestamp that can be used to track the health of the connection and prune inactive subscriptions.

### `app/models/orders.py`

This file defines the SQLAlchemy model for representing trading orders within the application, along with various enums that define order characteristics like type, side, status, and time in force.

#### Enums:

*   **`OrderType`**: Enumerates the supported order types (`MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`, `TAKE_PROFIT`).
*   **`OrderSide`**: Specifies the side of the order (`BUY`, `SELL`).
*   **`OrderStatus`**: Defines the lifecycle states of an order (`PENDING`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED`).
*   **`TimeInForce`**: Defines how long an order will remain active before it is executed or expires (`GTC`, `IOC`, `FOK`, `DAY`).

#### Models:

*   **`Order`**: Represents a single trading order placed by a user.
    *   **Purpose**: To track the details, lifecycle, and financial aspects of every trade request.
    *   **Fields**:
        *   `id`: Unique identifier for the order.
        *   `user_id`: Foreign key to the `User` who placed the order.
        *   `symbol`: The financial instrument to be traded.
        *   `order_type`: The type of the order (from `OrderType` enum).
        *   `side`: The side of the order (from `OrderSide` enum).
        *   `quantity`: The total number of shares/units to be traded.
        *   `filled_quantity`: The number of shares/units that have been filled.
        *   `price`: The limit price for `LIMIT` and `STOP_LIMIT` orders.
        *   `stop_price`: The trigger price for `STOP` and `STOP_LIMIT` orders.
        *   `average_fill_price`: The average price at which the order was filled.
        *   `status`: The current status of the order (from `OrderStatus` enum).
        *   `time_in_force`: The time-in-force policy for the order (from `TimeInForce` enum).
        *   `reserved_amount`: The amount of cash reserved for a `BUY` order.
        *   `estimated_cost`: The estimated cost of the order.
        *   `total_fees`: The total fees associated with the order.
        *   `idempotency_key`: A unique key to prevent duplicate order submissions.
        *   `related_order_id`, `parent_order_id`: For linking related orders (e.g., OCO, split orders).
        *   `created_at`, `updated_at`, `executed_at`, `canceled_at`, `expires_at`: Timestamps for various lifecycle events.
        *   `rejection_reason`: A reason for why an order was rejected.
    *   **Relationships**:
        *   `user`: Many-to-one relationship with `User`.
        *   `transactions`: One-to-many relationship with `StockTransaction`.
        *   `related_order`: Self-referencing relationship for linked orders.
    *   **Properties**:
        *   `remaining_quantity`: Calculated property for the unfilled portion of the order.
        *   `is_active`: Boolean property to check if the order is in a pending or partially filled state.
        *   `fill_percentage`: Calculated property for the percentage of the order that has been filled.
