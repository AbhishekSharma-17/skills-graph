# Telephony & SIP

> Source: [docs.livekit.io/telephony](https://docs.livekit.io/telephony/) — SIP trunking, phone integration

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [SIP Trunks](#sip-trunks)
- [Dispatch Rules](#dispatch-rules)
- [Phone Numbers](#phone-numbers)
- [Inbound Calls](#inbound-calls)
- [Outbound Calls](#outbound-calls)
- [Call Features](#call-features)
- [Tested Providers](#tested-providers)
- [Common Patterns](#common-patterns)

---

## Overview

LiveKit's telephony platform bridges traditional phone networks (PSTN) with LiveKit rooms. AI agents can:

- Answer inbound phone calls
- Make outbound calls
- Transfer calls (warm and cold)
- Detect DTMF tones
- Integrate with existing SIP infrastructure

## Architecture

```
┌──────────┐    PSTN     ┌──────────────┐   SIP    ┌──────────────┐
│  Phone   │ ──────────► │  SIP Provider │ ───────► │  LiveKit SIP │
│  (User)  │             │  (Twilio etc) │          │   Service    │
└──────────┘             └──────────────┘          └──────┬───────┘
                                                          │
                                                    Dispatch Rule
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │  LiveKit Room │
                                                   │   + Agent     │
                                                   └──────────────┘
```

**Components:**
- **DID numbers** — Phone numbers from LiveKit or your SIP provider
- **LiveKit Server** — API and room management
- **LiveKit SIP** — Handles SIP signaling and media conversion

## SIP Trunks

Trunks connect SIP providers to LiveKit:

### Inbound Trunk

```python
from livekit import api

lk_api = api.LiveKitAPI()

trunk = await lk_api.sip.create_sip_inbound_trunk(
    api.CreateSIPInboundTrunkRequest(
        trunk=api.SIPInboundTrunkInfo(
            name="Main Inbound",
            numbers=["+14155551234"],           # Your DID numbers
            allowed_addresses=["1.2.3.4/32"],   # SIP provider IPs
        )
    )
)
```

### Outbound Trunk

```python
trunk = await lk_api.sip.create_sip_outbound_trunk(
    api.CreateSIPOutboundTrunkRequest(
        trunk=api.SIPOutboundTrunkInfo(
            name="Main Outbound",
            address="sip.twilio.com",
            numbers=["+14155551234"],
            auth_username="your-username",
            auth_password="your-password",
        )
    )
)
```

**Trunk properties:**
- `name` — Human-readable label
- `numbers` — Phone numbers associated with this trunk
- `allowed_addresses` — IP whitelist for security (inbound)
- `address` — SIP server address (outbound)
- `auth_username`/`auth_password` — SIP authentication (outbound)

## Dispatch Rules

Control how inbound calls are routed to rooms:

```python
rule = await lk_api.sip.create_sip_dispatch_rule(
    api.CreateSIPDispatchRuleRequest(
        trunk_ids=[trunk.sip_trunk_id],
        rule=api.SIPDispatchRule(
            dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                room_prefix="call-",       # Room name: call-{caller-number}
                pin="1234",                 # Optional PIN requirement
            ),
        ),
        attributes={"source": "phone"},    # Custom participant attributes
    )
)
```

**Rule types:**
- `dispatch_rule_individual` — Creates a unique room per call
- `dispatch_rule_direct` — Routes to a specific existing room

## Phone Numbers

### LiveKit-provisioned (US only)

```bash
# Via CLI
lk sip number list
lk sip number purchase --area-code 415
```

### Bring your own numbers

Use any SIP provider's numbers by configuring inbound/outbound trunks.

## Inbound Calls

When a call comes in:

1. SIP provider routes the call to LiveKit SIP
2. Dispatch rule determines the target room
3. A SIP participant is auto-created in the room
4. Your agent (via `@RtcSession.on("session")`) receives the participant

```python
@RtcSession.on("session")
async def on_session(session: RtcSession):
    agent_session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:voice-id",
        vad=silero.VAD.load(),
    )

    await agent_session.start(
        room=session.room,
        agent=Agent(instructions="You are a phone receptionist for Acme Corp."),
        room_options=room_io.RoomOptions(
            participant_kinds=["SIP"],  # Accept SIP participants
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC()  # Phone-optimized
            ),
        ),
    )
```

## Outbound Calls

Initiate calls from your agent:

```python
# Create a SIP participant (makes the call)
participant = await lk_api.sip.create_sip_participant(
    api.CreateSIPParticipantRequest(
        sip_trunk_id=outbound_trunk_id,
        sip_call_to="+14155559876",
        room_name="outbound-call-123",
        participant_identity="callee",
        participant_name="Customer",
    )
)
```

**As a tool:**

```python
@function_tool()
async def call_customer(context: RunContext, phone_number: str) -> str:
    """Call a customer on their phone number."""
    participant = await lk_api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            room_name=context.session.room.name,
            participant_identity="customer",
        )
    )
    return f"Calling {phone_number}..."
```

## Call Features

### DTMF (Touchtone)

```python
# Detect DTMF tones from callers
@session.on("dtmf_received")
def on_dtmf(digits: str, participant):
    print(f"DTMF received: {digits}")
```

### Call Transfer

**Cold transfer** (blind):

```python
@function_tool()
async def transfer_call(context: RunContext, destination: str) -> str:
    """Transfer the caller to another number."""
    await lk_api.sip.transfer_sip_participant(
        api.TransferSIPParticipantRequest(
            room_name=context.session.room.name,
            participant_identity="caller",
            transfer_to=destination,
        )
    )
    return f"Call transferred to {destination}"
```

**Warm transfer** (attended):

```python
# 1. Add the transfer target to the room
# 2. Brief the target
# 3. Then transfer
```

### Noise Cancellation

Krisp AI-powered noise cancellation, auto-selects telephony-optimized variant:

```python
room_io.AudioInputOptions(
    noise_cancellation=noise_cancellation.BVC()
    # Automatically uses telephony variant for SIP participants
)
```

### Caller ID

```python
# Set outbound caller ID
api.CreateSIPParticipantRequest(
    sip_call_to="+14155559876",
    numbers=["+14155551234"],  # Caller ID number
)
```

## Tested Providers

| Provider | Status | Notes |
|----------|--------|-------|
| Twilio | Tested | Most popular, excellent docs |
| Telnyx | Tested | Good pricing |
| Plivo | Tested | Global coverage |
| Exotel | Tested | India/SE Asia |
| Wavix | Tested | Affordable |

LiveKit SIP is designed to work with all SIP providers, though only the above have been formally tested.

## Supported SIP Features

| Feature | Supported |
|---------|-----------|
| UDP/TCP/TLS transport | Yes |
| DTMF (RFC 2833/4733) | Yes |
| Cold transfer (REFER) | Yes |
| Warm transfer | Yes |
| Caller ID | Yes |
| RTP / SRTP | Yes |
| SIP Registration | No |
| SIPREC | No |
| Video over SIP | No |
| TLS REFER | No |

## Common Patterns

### IVR Navigation

```python
@function_tool()
async def navigate_ivr(context: RunContext, dtmf_digits: str) -> str:
    """Send DTMF tones to navigate an IVR menu."""
    await context.session.room.local_participant.publish_dtmf(dtmf_digits)
    return f"Sent DTMF: {dtmf_digits}"
```

### Recording Consent

```python
consent_task = Task(
    instructions="""This call may be recorded for quality purposes.
    Ask the caller if they consent to recording.
    You must get explicit verbal consent before proceeding.""",
    output_type=ConsentResult,
)
```

### Region Pinning

```python
# Pin trunk to specific geographic region
api.SIPInboundTrunkInfo(
    name="EU Trunk",
    numbers=["+442012345678"],
    allowed_regions=["eu-west-1"],
)
```
