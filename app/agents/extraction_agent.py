"""
Extraction Agent for DealFlow AI Copilot.

Processes pitch deck PDFs using vision + text analysis to extract structured
financial data, company information, and traction metrics.

Capabilities:
- PDF page-by-page vision analysis
- Text extraction and parsing
- Financial data normalization
- Data quality validation
- Inconsistency flagging
"""

import json
from typing import Any, Optional

from PIL import Image

from app.agents.base import BaseAgent
from app.models.schemas import (
    CompetitorInfo,
    ConfidenceLevel,
    DealStage,
    ExtractionResult,
    FinancialMetrics,
    FounderInfo,
    MarketData,
    MonetaryValue,
    TeamInfo,
    TractionMetrics,
    UnitEconomics,
)
from app.utils.exceptions import AnalysisError, ExtractionError
from app.utils.logger import logger

# Import prompts
import sys
sys.path.insert(0, ".")
from prompts.extraction_prompts import (
    EXTRACTION_MAIN_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    FINANCIAL_VALIDATION_PROMPT,
    VISION_EXTRACTION_PROMPT,
)


class ExtractionAgent(BaseAgent[ExtractionResult]):
    """
    Agent responsible for extracting structured data from pitch decks.

    Uses Gemini's vision capabilities to parse:
    - Financial tables and charts
    - Company information
    - Team details
    - Market data
    - Traction metrics

    Example:
        ```python
        agent = ExtractionAgent()
        result = await agent.run(
            images=pdf_images,
            text_content=extracted_text
        )
        print(result.company_name)
        print(result.financials.revenue)
        ```
    """

    @property
    def name(self) -> str:
        return "ExtractionAgent"

    async def execute(
        self,
        images: Optional[list[Image.Image]] = None,
        text_content: Optional[str] = None,
        company_name_hint: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Execute extraction from pitch deck content.

        Args:
            images: List of PIL Images (one per PDF page)
            text_content: Extracted text from the PDF
            company_name_hint: Optional hint for company name

        Returns:
            ExtractionResult with all extracted data

        Raises:
            ExtractionError: If extraction fails
        """
        if not images and not text_content:
            raise ExtractionError(
                message="No content provided for extraction",
                error_code="EXTRACTION_NO_CONTENT",
            )

        logger.info(
            f"[{self.name}] Starting extraction: "
            f"{len(images) if images else 0} images, "
            f"{len(text_content) if text_content else 0} chars text"
        )

        # Step 1: Vision analysis (if images provided)
        vision_data = {}
        if images:
            vision_data = await self._extract_from_images(images)
            logger.info(f"[{self.name}] Vision extraction complete")

        # Step 2: Text analysis
        text_data = {}
        if text_content:
            text_data = await self._extract_from_text(text_content, company_name_hint)
            logger.info(f"[{self.name}] Text extraction complete")

        # Step 3: Merge and validate
        merged_data = self._merge_extractions(vision_data, text_data)
        logger.info(f"[{self.name}] Data merged")

        # Step 4: Build result model
        result = self._build_result(merged_data, len(images) if images else 0)

        # Step 5: Quality assessment
        result = self._assess_quality(result)

        logger.info(
            f"[{self.name}] Extraction complete: {result.company_name}, "
            f"confidence={result.extraction_confidence:.2f}"
        )

        return result

    async def _extract_from_images(
        self,
        images: list[Image.Image],
    ) -> dict[str, Any]:
        """Extract data from pitch deck images using vision."""
        # Process in batches to handle large decks
        batch_size = 5
        all_extractions: list[dict[str, Any]] = []

        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(images) + batch_size - 1) // batch_size

            logger.debug(
                f"[{self.name}] Processing image batch {batch_num}/{total_batches}"
            )

            # Combine vision analysis with extraction prompt
            prompt = f"""{VISION_EXTRACTION_PROMPT}

{EXTRACTION_MAIN_PROMPT}"""

            response = await self.client.analyze_with_vision(
                images=batch,
                text=f"Pitch deck pages {i + 1} to {i + len(batch)}",
                prompt=prompt,
                model="pro",
                temperature=0.1,
            )

            # Parse response as JSON
            try:
                batch_data = self.client._extract_json_from_response(response)
                all_extractions.append(batch_data)
            except json.JSONDecodeError:
                logger.warning(
                    f"[{self.name}] Could not parse batch {batch_num} as JSON"
                )
                # Store raw text for later processing
                all_extractions.append({"_raw_text": response})

        # Merge all batch extractions
        return self._merge_batch_extractions(all_extractions)

    async def _extract_from_text(
        self,
        text_content: str,
        company_name_hint: Optional[str] = None,
    ) -> dict[str, Any]:
        """Extract data from text content."""
        hint_text = ""
        if company_name_hint:
            hint_text = f"\nNote: The company name is likely '{company_name_hint}'.\n"

        prompt = f"""{EXTRACTION_SYSTEM_PROMPT}

{hint_text}

PITCH DECK TEXT CONTENT:
{text_content[:50000]}  # Limit text length

{EXTRACTION_MAIN_PROMPT}"""

        try:
            result = await self.client.generate_structured(
                prompt=prompt,
                response_schema=self._get_extraction_schema(),
                model="pro",
                temperature=0.1,
            )
            return result
        except Exception as e:
            logger.warning(f"[{self.name}] Text extraction error: {e}")
            return {}

    def _merge_batch_extractions(
        self,
        extractions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Merge multiple extraction batches into one."""
        if not extractions:
            return {}

        # Start with first extraction
        merged = extractions[0].copy() if extractions[0] else {}

        for extraction in extractions[1:]:
            if not extraction or "_raw_text" in extraction:
                continue

            # Merge each field
            for key, value in extraction.items():
                if key not in merged or merged[key] is None:
                    merged[key] = value
                elif isinstance(value, list) and isinstance(merged.get(key), list):
                    # Combine lists, removing duplicates
                    existing = set(str(x) for x in merged[key])
                    for item in value:
                        if str(item) not in existing:
                            merged[key].append(item)
                elif isinstance(value, dict) and isinstance(merged.get(key), dict):
                    # Recursively merge dicts
                    merged[key] = self._merge_dicts(merged[key], value)

        return merged

    def _merge_dicts(
        self,
        dict1: dict[str, Any],
        dict2: dict[str, Any],
    ) -> dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = dict1.copy()

        for key, value in dict2.items():
            if key not in result or result[key] is None:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._merge_dicts(result[key], value)
            elif isinstance(value, list) and isinstance(result.get(key), list):
                result[key] = list(set(result[key] + value))

        return result

    def _merge_extractions(
        self,
        vision_data: dict[str, Any],
        text_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge vision and text extractions, preferring vision for numerical data."""
        # Start with text data as base
        merged = text_data.copy() if text_data else {}

        # Overlay vision data, which is often more accurate for numbers
        if vision_data:
            merged = self._merge_dicts(merged, vision_data)

        return merged

    def _build_result(
        self,
        data: dict[str, Any],
        page_count: int,
    ) -> ExtractionResult:
        """Build ExtractionResult from raw extracted data."""
        # Helper to safely get nested values
        def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
            for key in keys:
                if isinstance(d, dict):
                    d = d.get(key, default)
                else:
                    return default
            return d

        # Helper to build MonetaryValue
        def build_monetary(d: Optional[dict]) -> Optional[MonetaryValue]:
            if not d or not isinstance(d, dict):
                return None
            amount = d.get("amount")
            if amount is None:
                return None
            return MonetaryValue(
                amount=float(amount),
                currency=d.get("currency", "USD"),
                unit=d.get("unit", ""),
            )

        # Build team info
        founders = []
        for f in safe_get(data, "team", "founders", default=[]) or []:
            if isinstance(f, dict):
                founders.append(
                    FounderInfo(
                        name=f.get("name", "Unknown"),
                        title=f.get("title", ""),
                        background=f.get("background"),
                        previous_companies=f.get("previous_companies", []),
                        education=f.get("education"),
                    )
                )

        team = TeamInfo(
            founders=founders,
            total_employees=safe_get(data, "team", "total_employees"),
            employee_growth_rate=safe_get(data, "team", "employee_growth_rate"),
            key_hires=safe_get(data, "team", "key_hires", default=[]) or [],
            open_roles=safe_get(data, "team", "open_roles", default=[]) or [],
            team_gaps=safe_get(data, "team", "team_gaps", default=[]) or [],
        )

        # Build financial metrics
        financials = FinancialMetrics(
            revenue=build_monetary(safe_get(data, "financials", "revenue")),
            revenue_growth_rate=safe_get(data, "financials", "revenue_growth_rate"),
            mrr=build_monetary(safe_get(data, "financials", "mrr")),
            arr=build_monetary(safe_get(data, "financials", "arr")),
            gross_margin=safe_get(data, "financials", "gross_margin"),
            net_margin=safe_get(data, "financials", "net_margin"),
            ebitda=build_monetary(safe_get(data, "financials", "ebitda")),
            ebitda_margin=safe_get(data, "financials", "ebitda_margin"),
            cash_on_hand=build_monetary(safe_get(data, "financials", "cash_on_hand")),
            monthly_burn_rate=build_monetary(
                safe_get(data, "financials", "monthly_burn_rate")
            ),
            runway_months=safe_get(data, "financials", "runway_months"),
            total_raised=build_monetary(safe_get(data, "financials", "total_raised")),
            current_round_size=build_monetary(
                safe_get(data, "financials", "current_round_size")
            ),
            pre_money_valuation=build_monetary(
                safe_get(data, "financials", "pre_money_valuation")
            ),
            revenue_history=safe_get(data, "financials", "revenue_history", default=[])
            or [],
        )

        # Build unit economics
        unit_economics = UnitEconomics(
            cac=build_monetary(safe_get(data, "unit_economics", "cac")),
            ltv=build_monetary(safe_get(data, "unit_economics", "ltv")),
            ltv_cac_ratio=safe_get(data, "unit_economics", "ltv_cac_ratio"),
            payback_period_months=safe_get(
                data, "unit_economics", "payback_period_months"
            ),
            arpu=build_monetary(safe_get(data, "unit_economics", "arpu")),
            net_revenue_retention=safe_get(
                data, "unit_economics", "net_revenue_retention"
            ),
            gross_revenue_retention=safe_get(
                data, "unit_economics", "gross_revenue_retention"
            ),
            churn_rate=safe_get(data, "unit_economics", "churn_rate"),
        )

        # Build market data
        market = MarketData(
            tam=build_monetary(safe_get(data, "market", "tam")),
            sam=build_monetary(safe_get(data, "market", "sam")),
            som=build_monetary(safe_get(data, "market", "som")),
            tam_source=safe_get(data, "market", "tam_source"),
            market_growth_rate=safe_get(data, "market", "market_growth_rate"),
            market_description=safe_get(data, "market", "market_description"),
        )

        # Build traction metrics
        traction = TractionMetrics(
            total_customers=safe_get(data, "traction", "total_customers"),
            customer_growth_rate=safe_get(data, "traction", "customer_growth_rate"),
            enterprise_customers=safe_get(data, "traction", "enterprise_customers"),
            smb_customers=safe_get(data, "traction", "smb_customers"),
            notable_customers=safe_get(data, "traction", "notable_customers", default=[])
            or [],
            total_users=safe_get(data, "traction", "total_users"),
            mau=safe_get(data, "traction", "mau"),
            dau=safe_get(data, "traction", "dau"),
            user_growth_rate=safe_get(data, "traction", "user_growth_rate"),
            engagement_rate=safe_get(data, "traction", "engagement_rate"),
            conversion_rate=safe_get(data, "traction", "conversion_rate"),
            gmv=build_monetary(safe_get(data, "traction", "gmv")),
        )

        # Build competitors
        competitors = []
        for c in data.get("competitors", []) or []:
            if isinstance(c, dict):
                competitors.append(
                    CompetitorInfo(
                        name=c.get("name", "Unknown"),
                        description=c.get("description"),
                        funding_raised=build_monetary(c.get("funding_raised")),
                        market_position=c.get("market_position"),
                        key_differentiators=c.get("key_differentiators", []),
                    )
                )

        # Map stage string to enum
        stage_mapping = {
            "pre_seed": DealStage.PRE_SEED,
            "seed": DealStage.SEED,
            "series_a": DealStage.SERIES_A,
            "series_b": DealStage.SERIES_B,
            "series_c": DealStage.SERIES_C,
            "growth": DealStage.GROWTH,
            "late_stage": DealStage.LATE_STAGE,
        }
        stage_str = data.get("stage", "").lower().replace(" ", "_").replace("-", "_")
        stage = stage_mapping.get(stage_str)

        return ExtractionResult(
            company_name=data.get("company_name", "Unknown Company"),
            tagline=data.get("tagline"),
            description=data.get("description"),
            website=data.get("website"),
            founded_year=data.get("founded_year"),
            headquarters=data.get("headquarters"),
            industry=data.get("industry"),
            sector=data.get("sector"),
            business_model=data.get("business_model"),
            stage=stage,
            team=team,
            financials=financials,
            unit_economics=unit_economics,
            market=market,
            traction=traction,
            competitors=competitors,
            competitive_advantages=data.get("competitive_advantages", []) or [],
            product_description=data.get("product_description"),
            key_features=data.get("key_features", []) or [],
            technology_stack=data.get("technology_stack", []) or [],
            funding_ask=build_monetary(data.get("funding_ask")),
            use_of_funds=data.get("use_of_funds", []) or [],
            extraction_confidence=data.get("extraction_confidence", 0.5),
            data_quality_flags=data.get("data_quality_flags", []) or [],
            missing_data_points=data.get("missing_data_points", []) or [],
            source_page_count=page_count,
        )

    def _assess_quality(self, result: ExtractionResult) -> ExtractionResult:
        """Assess data quality and update confidence score."""
        quality_issues: list[str] = list(result.data_quality_flags)
        missing_points: list[str] = list(result.missing_data_points)

        # Check critical fields
        if not result.company_name or result.company_name == "Unknown Company":
            quality_issues.append("Company name not found")

        if not result.financials.revenue and not result.financials.arr:
            missing_points.append("Revenue/ARR")

        if not result.financials.revenue_growth_rate:
            missing_points.append("Growth rate")

        if not result.market.tam:
            missing_points.append("TAM/Market size")

        if not result.team.founders:
            missing_points.append("Founder information")

        if not result.financials.current_round_size and not result.funding_ask:
            missing_points.append("Funding ask")

        # Check for inconsistencies
        if result.financials.mrr and result.financials.arr:
            mrr_normalized = result.financials.mrr.normalized_amount
            arr_normalized = result.financials.arr.normalized_amount
            expected_arr = mrr_normalized * 12

            if arr_normalized > 0:
                variance = abs(expected_arr - arr_normalized) / arr_normalized
                if variance > 0.1:  # More than 10% difference
                    quality_issues.append(
                        f"MRR/ARR mismatch: MRR×12=${expected_arr:,.0f} vs ARR=${arr_normalized:,.0f}"
                    )

        # Calculate confidence score
        base_confidence = 0.8
        confidence_penalty = (len(quality_issues) * 0.1) + (len(missing_points) * 0.05)
        final_confidence = max(0.1, min(1.0, base_confidence - confidence_penalty))

        # Update result
        result.data_quality_flags = quality_issues
        result.missing_data_points = missing_points
        result.extraction_confidence = final_confidence

        return result

    def _get_extraction_schema(self) -> dict[str, Any]:
        """Get JSON schema for structured extraction."""
        return {
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "tagline": {"type": ["string", "null"]},
                "description": {"type": ["string", "null"]},
                "website": {"type": ["string", "null"]},
                "founded_year": {"type": ["integer", "null"]},
                "headquarters": {"type": ["string", "null"]},
                "industry": {"type": ["string", "null"]},
                "sector": {"type": ["string", "null"]},
                "business_model": {"type": ["string", "null"]},
                "stage": {"type": ["string", "null"]},
                "team": {"type": "object"},
                "financials": {"type": "object"},
                "unit_economics": {"type": "object"},
                "market": {"type": "object"},
                "traction": {"type": "object"},
                "competitors": {"type": "array"},
                "competitive_advantages": {"type": "array"},
                "product_description": {"type": ["string", "null"]},
                "key_features": {"type": "array"},
                "technology_stack": {"type": "array"},
                "funding_ask": {"type": ["object", "null"]},
                "use_of_funds": {"type": "array"},
                "extraction_confidence": {"type": "number"},
                "data_quality_flags": {"type": "array"},
                "missing_data_points": {"type": "array"},
            },
            "required": ["company_name"],
        }
