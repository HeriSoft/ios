import { router, useLocalSearchParams } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import { View } from "react-native";
import { ProductDetail } from "../../src/components/ProductDetail";
import { Button, EmptyState, ErrorState, LoadingState } from "../../src/components/ui";
import { ProductInfo } from "../../src/core/basics";
import { lookupProduct } from "../../src/core/openFoodFacts";

type State = { kind: "loading" } | { kind: "found"; product: ProductInfo } | { kind: "notFound" } | { kind: "failed"; message: string };

export default function LookupScreen() {
  const { code } = useLocalSearchParams<{ code: string }>();
  const [state, setState] = useState<State>({ kind: "loading" });
  const load = useCallback(() => {
    setState({ kind: "loading" });
    lookupProduct(code)
      .then((p) => setState(p ? { kind: "found", product: p } : { kind: "notFound" }))
      .catch((e: Error) => setState({ kind: "failed", message: e.message || "Không kết nối được. Kiểm tra mạng và thử lại." }));
  }, [code]);
  useEffect(load, [load]);

  if (state.kind === "found") return <ProductDetail product={state.product} />;
  if (state.kind === "loading") return <LoadingState label={`Đang tra cứu mã ${code}…`} />;
  if (state.kind === "failed") return <ErrorState message={state.message} onRetry={load} />;
  return (
    <EmptyState icon="🔍" title="Không tìm thấy sản phẩm"
      message={`Mã ${code} chưa có trong cơ sở dữ liệu Open Food Facts. Bạn có thể quét nhãn dinh dưỡng hoặc tự nhập lượng calo.`}
      action={
        <View style={{ gap: 10 }}>
          <Button label="Quét nhãn dinh dưỡng" onPress={() => router.push({ pathname: "/label", params: { code } })} />
          <Button label="Nhập thủ công" variant="secondary" onPress={() => router.push({ pathname: "/manual", params: { code } })} />
        </View>
      } />
  );
}
