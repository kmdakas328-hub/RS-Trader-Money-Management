from dataclasses import dataclass


@dataclass
class TradeResult:
    trade_number: int
    result: str
    amount: float
    profit_loss: float
    balance: float


class MoneyCalculator:

    def __init__(
        self,
        starting_capital: float = 114.0,
        payout: float = 85.0,
        profit_target_percent: float = 5.0,
        stop_loss_percent: float = 7.5,
        max_loss_streak: int = 3,
        planned_wins: int = 5,
        base_risk_percent: float = 1.0,
    ):

        self.starting_capital = float(starting_capital)
        self.balance = float(starting_capital)

        self.payout = float(payout) / 100.0

        self.profit_target_percent = float(
            profit_target_percent
        )

        self.stop_loss_percent = float(
            stop_loss_percent
        )

        self.max_loss_streak = int(
            max_loss_streak
        )

        self.planned_wins = 5

        self.base_risk_percent = float(
            base_risk_percent
        )

        self.total_profit_loss = 0.0
        self.trade_number = 0

        self.win_count = 0
        self.loss_count = 0

        self.loss_streak = 0
        self.unrecovered_loss = 0.0

        self.history = []

    @property
    def profit_target_amount(self):
        return round(
            self.starting_capital
            * self.profit_target_percent
            / 100.0,
            2
        )

    @property
    def stop_loss_amount(self):
        return round(
            self.starting_capital
            * self.stop_loss_percent
            / 100.0,
            2
        )

    @property
    def trade_percent(self):
        return (
            self.profit_target_percent
            / 5.0
        )

    @property
    def is_profit_target_reached(self):
        return (
            self.total_profit_loss
            >= self.profit_target_amount
        )

    @property
    def is_stop_loss_reached(self):
        return (
            self.unrecovered_loss
            >= self.stop_loss_amount
            or
            self.loss_streak
            >= self.max_loss_streak
        )

    @property
    def session_stopped(self):
        return (
            self.is_profit_target_reached
            or
            self.is_stop_loss_reached
        )

    def get_status(self):

        if self.is_profit_target_reached:
            return "PROFIT TARGET REACHED"

        if self.is_stop_loss_reached:
            return "STOP LOSS REACHED"

        if self.loss_streak > 0:
            return (
                f"RECOVERY MODE "
                f"{self.loss_streak}/{self.max_loss_streak}"
            )

        return "ACTIVE"

    def calculate_normal_amount(self):

        amount = (
            self.balance
            * self.trade_percent
            / 100.0
        )

        return round(
            amount,
            2
        )

    def calculate_recovery_amount(self):

        if self.unrecovered_loss <= 0:
            return self.calculate_normal_amount()

        remaining_stop_room = (
            self.stop_loss_amount
            - self.unrecovered_loss
        )

        if remaining_stop_room <= 0:
            return 0.0

        desired_profit = (
            self.balance
            * self.trade_percent
            / 100.0
        )

        recovery_amount = (
            self.unrecovered_loss
            + desired_profit
        ) / self.payout

        amount = min(
            recovery_amount,
            remaining_stop_room
        )

        return round(
            max(
                0.0,
                amount
            ),
            2
        )

    def calculate_next_amount(self):

        if self.session_stopped:
            return 0.0

        if self.loss_streak == 0:
            amount = self.calculate_normal_amount()
        else:
            amount = self.calculate_recovery_amount()

        return round(
            max(
                0.0,
                amount
            ),
            2
        )

    def record_trade(self, result: str):

        result = result.upper().strip()

        if result not in ("WIN", "LOSS"):
            raise ValueError(
                "Result must be WIN or LOSS."
            )

        if self.session_stopped:
            raise RuntimeError(
                "The trading session has already stopped."
            )

        amount = self.calculate_next_amount()

        if amount <= 0:
            raise RuntimeError(
                "No valid trade amount is available."
            )

        if result == "WIN":

            profit_loss = round(
                amount * self.payout,
                2
            )

            self.balance = round(
                self.balance + profit_loss,
                2
            )

            self.win_count += 1
            self.loss_streak = 0

            if self.unrecovered_loss > 0:

                self.unrecovered_loss = round(
                    max(
                        0.0,
                        self.unrecovered_loss
                        - profit_loss
                    ),
                    2
                )

        else:

            profit_loss = round(
                -amount,
                2
            )

            self.balance = round(
                self.balance - amount,
                2
            )

            self.loss_count += 1
            self.loss_streak += 1

            self.unrecovered_loss = round(
                self.unrecovered_loss + amount,
                2
            )

        self.total_profit_loss = round(
            self.balance
            - self.starting_capital,
            2
        )

        self.trade_number += 1

        trade = TradeResult(
            trade_number=self.trade_number,
            result=result,
            amount=amount,
            profit_loss=profit_loss,
            balance=self.balance,
        )

        self.history.append(
            trade
        )

        return trade

    def reset(self):

        self.balance = float(
            self.starting_capital
        )

        self.total_profit_loss = 0.0

        self.trade_number = 0

        self.win_count = 0
        self.loss_count = 0

        self.loss_streak = 0

        self.unrecovered_loss = 0.0

        self.history.clear()

    def update_settings(
        self,
        starting_capital: float,
        payout: float,
        profit_target_percent: float,
        stop_loss_percent: float,
        max_loss_streak: int,
        planned_wins: int,
        base_risk_percent: float = 1.0,
    ):

        if starting_capital <= 0:
            raise ValueError(
                "Starting capital must be greater than zero."
            )

        if not 1 <= payout <= 100:
            raise ValueError(
                "Payout must be between 1 and 100."
            )

        if profit_target_percent <= 0:
            raise ValueError(
                "Profit target must be greater than zero."
            )

        if stop_loss_percent <= 0:
            raise ValueError(
                "Stop loss must be greater than zero."
            )

        if max_loss_streak < 1:
            raise ValueError(
                "Maximum loss streak must be at least 1."
            )

        if base_risk_percent <= 0:
            raise ValueError(
                "Base risk percentage must be greater than zero."
            )

        self.starting_capital = float(
            starting_capital
        )

        self.payout = float(
            payout
        ) / 100.0

        self.profit_target_percent = float(
            profit_target_percent
        )

        self.stop_loss_percent = float(
            stop_loss_percent
        )

        self.max_loss_streak = int(
            max_loss_streak
        )

        self.planned_wins = 5

        self.base_risk_percent = float(
            base_risk_percent
        )

        self.reset()
