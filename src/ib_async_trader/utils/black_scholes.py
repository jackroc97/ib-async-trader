import numpy as np

from datetime import datetime
from scipy.stats import norm


class BlackScholes:
    """
    A utility class for implementing the Black-Scholes options pricing model.
    See https://www.macroption.com/black-scholes-formula/ for more information
    on these forumulas.
    """
    DAYS_PER_YEAR = 365
    SECONDS_PER_DAY = 86400
    
    
    @classmethod
    def call_put_price(cls, S: float, K: float, t: float, sigma: float, 
                       r: float = 0.25, q: float = 0) -> tuple[float, float]:
        """
        Calculate the Black-Scholes call and put price for an options 
        contract given an underlying market price, contract strike price, 
        time to contract expiration, and underlying IV.
        
        Args:
            S (float): The price of the underlying.
            K (float): The strike price of the options contract.
            t (float): The time to expiration, expressed in fractions of a year 
            (see `time_to_expiration_years`).
            sigma (float): The implied volatility of the underlying.
            r (float, optional): The risk-free rate. Defaults to 0.25.
            q (float, optional): The dividend yeild. Defaults to 0.

        Returns:
            tuple[float, float]: The call and put price for a contract with the 
            given strike and expiration.
        """
        d1 = cls._calc_d1(S, K, sigma, t, r, q)
        d2 = cls._calc_d2(d1, sigma, t)
    
        c = S * cls._N(d1) - K * np.exp(-r * t) * cls._N(d2)
        p = K * np.exp(-r * t) * cls._N(-d2) - S * cls._N(-d1)
    
        return c, p
    
    
    @classmethod
    def time_to_expiration_years(cls, exp_dt: datetime, 
                                 t: datetime = datetime.now()) -> float:
        """
        Calculate the time to expiration in fractions of a year.

        Args:
            exp_dt (datetime): The expriation date of an options contract.
            t (datetime, optional): The "current" time for which to calculate 
            time to expiration. Defaults to datetime.now().

        Returns:
            float: The time between `exp_dt` and `t` expressed in fractions of a 
            year.
        """
        return (exp_dt - t).seconds / (cls.DAYS_PER_YEAR * cls.SECONDS_PER_DAY)
    
    
    @classmethod
    def std_dev_price_range(cls, S: float, t: float, sigma: float, N: int = 1, 
                            r: float = 0.25):
        """
        Get the standard deviation of price based on implied volatility of the 
        underlying.

        Args:
            S (float): The price of the underlying.
            t (float): The time to expiration, expressed in fractions of a year 
            (see `time_to_expiration_years`).
            sigma (float): The implied volatility of the underlying.
            N (int): Which standard deviation to calculate. Defaults to 1.
            r (float, optional): The risk-free rate. Defaults to 0.25.

        Returns:
            _type_: _description_
        """
        upper = S * np.exp(r * t + N * sigma * np.sqrt(t))
        lower = S * np.exp(r * t - N * sigma * np.sqrt(t))
        return lower, upper
    
    
    @classmethod
    def call_put_delta(cls, S: float, K: float, t: float, sigma: float,
                       r: float = 0.25, q: float = 0) -> tuple[float, float]:
        """
        Calculate the delta for a call or put given an underlying market price, 
        contract strike price, and time to contract expiration.

        Args:
            S (float): The price of the underlying.
            K (float): The strike price of the options contract.
            t (float): The time to expiration, expressed in fractions of a year 
            (see `time_to_expiration_years`).
            sigma (float): The implied volatility of the underlying.
            r (float, optional): The risk-free rate. Defaults to 0.25.
            q (float, optional): The dividend yeild. Defaults to 0.

        Returns:
            tuple[float, float]: The delta of a call or put contract with the
            given parameters.
        """
        d1 = cls._calc_d1(S, K, sigma, t, r)
        delta_call = np.exp(-q * t) * cls._N(d1)
        delta_put =  np.exp(-q * t) * (cls._N(d1) - 1)
        return delta_call, delta_put
        
    
    @classmethod
    def strike_for_delta(cls, delta: float, S: float, t: float,  sigma: float, 
                         r: float = 0.25, q: float = 0) -> float:
        """
        Get the strikes needed for a given delta on a contract. 

        Args:
            delta (float): The desired delta.
            S (float): The price of the underlying
            t (float): The time to expiration, expressed in fractions of a year 
            (see `time_to_expiration_years`).
            sigma (float): The implied volatility of the underlying.
            r (float, optional): The risk-free rate. Defaults to 0.25.
            q (float, optional): The dividend yeild. Defaults to 0.

        Returns:
            float: The strike price that will have the desired delta.
        """
        a = t * (r - q + (sigma**2 / 2))
        b = delta / np.exp(-q * t)
        denom = np.exp(sigma * np.sqrt(t) * norm.ppf(b) - a)
        return S / denom
    
    
    @classmethod
    def _calc_d1(_, S: float, K: float, sigma: float, t: float, r: float, 
                 q: float = 0) -> float:
        num = np.log(S/K) + t * (r - q + ((sigma**2)/2))
        denom = sigma * np.sqrt(t)    
        return num/denom

    
    @classmethod
    def _calc_d2(_, d1: float, sigma: float, t: float) -> float:
        return d1 - sigma * np.sqrt(t)


    @classmethod
    def _N(_, x: float) -> float:
        return norm.cdf(x)
    